"""Lemon Squeezy integration for Cortex.

This module is credential-free by design: secrets are read from environment
variables at runtime and are never persisted in Cortex state. The adapter keeps
Lemon Squeezy-specific HTTP/webhook details outside the provider-neutral order
and payment engines.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

LEMON_SQUEEZY_API = "https://api.lemonsqueezy.com/v1"
API_KEY_ENV = "LEMON_SQUEEZY_API_KEY"
WEBHOOK_SECRET_ENV = "LEMON_SQUEEZY_WEBHOOK_SECRET"
STORE_ID_ENV = "LEMON_SQUEEZY_STORE_ID"
VARIANT_ID_ENV = "LEMON_SQUEEZY_VARIANT_ID"
TEST_MODE_ENV = "LEMON_SQUEEZY_TEST_MODE"

# Lemon Squeezy signs the raw webhook body with HMAC-SHA256 and sends the
# hexadecimal digest in X-Signature. No parsed field is trusted for signing.
SUPPORTED_EVENTS = {"order_created", "order_refunded"}


def _money(value: Any) -> Decimal | None:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not amount.is_finite() or amount <= 0:
        return None
    return amount.quantize(Decimal("0.01"))


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def is_test_mode() -> bool:
    return _bool_env(TEST_MODE_ENV, True)


def sign_webhook(raw_body: bytes, secret: str) -> str:
    """Return the Lemon Squeezy X-Signature value for tests/local fixtures."""
    if not isinstance(raw_body, (bytes, bytearray)) or not secret:
        raise ValueError("raw_body and webhook secret are required")
    return hmac.new(secret.encode("utf-8"), bytes(raw_body), hashlib.sha256).hexdigest()


def verify_webhook_signature(raw_body: bytes, signature: str | None, secret: str | None = None) -> bool:
    if not isinstance(raw_body, (bytes, bytearray)) or not signature:
        return False
    secret = secret or os.getenv(WEBHOOK_SECRET_ENV)
    if not secret:
        return False
    expected = sign_webhook(bytes(raw_body), secret)
    return hmac.compare_digest(expected, str(signature).strip())


def _parse_json(raw_body: bytes) -> dict[str, Any] | None:
    try:
        value = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return None
    return value if isinstance(value, dict) else None


def translate_webhook(raw_body: bytes, signature: str | None, secret: str | None = None) -> dict[str, Any]:
    """Translate a verified Lemon Squeezy order webhook into Cortex's contract.

    The returned event is suitable for the existing ``payment_webhook`` engine;
    this function does not mark an order paid and has no delivery authority.
    """
    if not verify_webhook_signature(raw_body, signature, secret):
        return {"ok": False, "status": 401, "error": "invalid Lemon Squeezy signature"}

    payload = _parse_json(raw_body)
    if payload is None:
        return {"ok": False, "status": 400, "error": "invalid JSON payload"}

    meta = payload.get("meta")
    data = payload.get("data")
    if not isinstance(meta, Mapping) or not isinstance(data, Mapping):
        return {"ok": False, "status": 400, "error": "invalid Lemon Squeezy event structure"}

    event_name = str(meta.get("event_name", "")).strip()
    if event_name not in SUPPORTED_EVENTS:
        return {"ok": False, "status": 400, "error": "unsupported Lemon Squeezy event"}

    attributes = data.get("attributes")
    if not isinstance(attributes, Mapping):
        return {"ok": False, "status": 400, "error": "missing order attributes"}

    custom_data = meta.get("custom_data")
    if not isinstance(custom_data, Mapping):
        custom_data = {}
    order_id = str(custom_data.get("order_id", "")).strip()
    if not order_id:
        return {"ok": False, "status": 400, "error": "missing Cortex order_id"}

    provider_order_id = str(data.get("id", "")).strip()
    if not provider_order_id:
        return {"ok": False, "status": 400, "error": "missing Lemon Squeezy order ID"}

    status = str(attributes.get("status", "")).strip().lower()
    if event_name == "order_refunded":
        return {
            "ok": True,
            "status": 200,
            "event_id": f"lemonsqueezy:{event_name}:{provider_order_id}",
            "event_type": event_name,
            "order_id": order_id,
            "transaction_id": f"lemonsqueezy-order:{provider_order_id}",
            "provider_order_id": provider_order_id,
            "refunded": True,
        }

    if status != "paid":
        return {"ok": False, "status": 409, "error": "Lemon Squeezy order is not paid"}

    amount = _money(attributes.get("total"))
    currency = str(attributes.get("currency", "")).strip().upper()
    # Lemon Squeezy monetary totals are represented in the order's currency's
    # minor units. Convert integer totals to major units for Cortex's order ledger.
    currency_total = attributes.get("total")
    if isinstance(currency_total, int) and amount is not None:
        amount = (Decimal(currency_total) / Decimal("100")).quantize(Decimal("0.01"))
    if amount is None or len(currency) != 3:
        return {"ok": False, "status": 400, "error": "invalid Lemon Squeezy amount or currency"}

    return {
        "ok": True,
        "status": 200,
        "event_id": f"lemonsqueezy:{event_name}:{provider_order_id}",
        "event_type": "payment.succeeded",
        "order_id": order_id,
        "transaction_id": f"lemonsqueezy-order:{provider_order_id}",
        "provider_order_id": provider_order_id,
        "amount": str(amount),
        "currency": currency,
    }


def _api_request(method: str, path: str, body: Mapping[str, Any] | None = None, *, timeout: float = 15.0) -> dict[str, Any]:
    """Call the Lemon Squeezy API using stdlib HTTPS; never log the API key."""
    api_key = os.getenv(API_KEY_ENV)
    if not api_key:
        raise RuntimeError(f"{API_KEY_ENV} is not configured")
    if not path.startswith("/"):
        path = "/" + path
    payload = None if body is None else json.dumps(body, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        LEMON_SQUEEZY_API + path,
        data=payload,
        method=method.upper(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        # Preserve provider status but not credentials or full request details.
        return {"ok": False, "status": int(error.code), "error": "Lemon Squeezy API request failed"}
    except (urllib.error.URLError, TimeoutError):
        return {"ok": False, "status": 503, "error": "Lemon Squeezy API unavailable"}
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"ok": False, "status": 502, "error": "invalid Lemon Squeezy API response"}
    return decoded if isinstance(decoded, dict) else {"ok": False, "status": 502, "error": "invalid Lemon Squeezy API response"}


def create_checkout(*, order_id: str, variant_id: str | None = None, email: str | None = None, custom_data: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Create a hosted Lemon Squeezy checkout for an existing Cortex order."""
    store_id = os.getenv(STORE_ID_ENV)
    variant_id = variant_id or os.getenv(VARIANT_ID_ENV)
    order_id = str(order_id or "").strip()
    if not store_id or not variant_id or not order_id:
        return {"ok": False, "status": 503, "error": "Lemon Squeezy store, variant, and Cortex order are required"}

    checkout_data: dict[str, Any] = {"custom": {"order_id": order_id}}
    if email:
        checkout_data["email"] = str(email).strip()
    if custom_data:
        checkout_data["custom"].update(dict(custom_data))
    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": checkout_data,
                "product_options": {"enabled_variants": [int(variant_id)]},
                "checkout_options": {"embed": False},
            },
            "relationships": {
                "store": {"data": {"type": "stores", "id": str(store_id)}},
                "variant": {"data": {"type": "variants", "id": str(variant_id)}},
            },
        }
    }
    result = _api_request("POST", "/checkouts", payload)
    if result.get("ok") is False and "status" in result:
        return result
    try:
        url = result["data"]["attributes"]["url"]
    except (KeyError, TypeError):
        return {"ok": False, "status": 502, "error": "Lemon Squeezy checkout URL missing"}
    return {"ok": True, "status": 200, "checkout_url": str(url), "request_id": uuid.uuid4().hex}
