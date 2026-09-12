"""Local Stripe connection and Checkout adapter for Cortex.

Secrets are stored outside Git in a local 0600 JSON file. The browser only
receives masked connection status; secret values are never returned to it.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import stat
import tempfile
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from payment_webhook import process_event

STRIPE_SECRET_ENV = "STRIPE_SECRET_KEY"
STRIPE_WEBHOOK_ENV = "STRIPE_WEBHOOK_SECRET"
CREDENTIALS_FILE = Path(".cortex_stripe_credentials.json")
STRIPE_API = "https://api.stripe.com/v1"
SIGNATURE_TOLERANCE_SECONDS = 300
MAX_SECRET_LENGTH = 512


def _credential_path() -> Path:
    configured = os.getenv("CORTEX_STRIPE_CREDENTIALS_FILE")
    return Path(configured) if configured else CREDENTIALS_FILE


def _read_credentials() -> dict[str, str]:
    path = _credential_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if k in {STRIPE_SECRET_ENV, STRIPE_WEBHOOK_ENV} and isinstance(v, str)}


def _write_credentials(secret_key: str, webhook_secret: str) -> None:
    path = _credential_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".stripe-credentials-", dir=str(path.parent))
    try:
        os.chmod(temp_name, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({STRIPE_SECRET_ENV: secret_key, STRIPE_WEBHOOK_ENV: webhook_secret}, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    finally:
        try:
            os.remove(temp_name)
        except OSError:
            pass


def connect(secret_key: str, webhook_secret: str = "") -> dict[str, object]:
    secret_key = str(secret_key or "").strip()
    webhook_secret = str(webhook_secret or "").strip()
    if not secret_key.startswith(("sk_test_", "sk_live_")) or len(secret_key) > MAX_SECRET_LENGTH:
        return {"ok": False, "status": 400, "error": "invalid Stripe secret key format"}
    if webhook_secret and len(webhook_secret) > MAX_SECRET_LENGTH:
        return {"ok": False, "status": 400, "error": "invalid webhook secret"}
    result = test_connection(secret_key)
    if not result["ok"]:
        return result
    _write_credentials(secret_key, webhook_secret)
    return status()


def disconnect() -> dict[str, object]:
    path = _credential_path()
    try:
        path.unlink(missing_ok=True)
    except OSError:
        return {"ok": False, "status": 503, "error": "could not remove local Stripe credentials"}
    return {"ok": True, "status": 200, "connected": False}


def _key() -> str:
    return os.getenv(STRIPE_SECRET_ENV, "").strip() or _read_credentials().get(STRIPE_SECRET_ENV, "").strip()


def _webhook_secret() -> str:
    return os.getenv(STRIPE_WEBHOOK_ENV, "").strip() or _read_credentials().get(STRIPE_WEBHOOK_ENV, "").strip()


def _stripe_request(path: str, *, data: bytes | None = None, method: str = "GET", secret_key: str | None = None) -> tuple[int, dict]:
    key = secret_key or _key()
    if not key:
        return 503, {"ok": False, "error": "Stripe is not connected"}
    request = Request(f"{STRIPE_API}/{path.lstrip('/')}", data=data, method=method)
    token = base64.b64encode((key + ":").encode()).decode()
    request.add_header("Authorization", f"Basic {token}")
    if data is not None:
        request.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return response.status, payload if isinstance(payload, dict) else {}
    except HTTPError as error:
        try:
            payload = json.loads(error.read().decode("utf-8"))
        except Exception:
            payload = {"error": {"message": "Stripe request failed"}}
        message = payload.get("error", {}).get("message", "Stripe request failed")
        return error.code, {"ok": False, "error": str(message)}
    except (URLError, TimeoutError, OSError, ValueError):
        return 503, {"ok": False, "error": "Stripe connection unavailable"}


def test_connection(secret_key: str | None = None) -> dict[str, object]:
    status_code, payload = _stripe_request("account", secret_key=secret_key)
    if status_code < 200 or status_code >= 300:
        return {"ok": False, "status": status_code, "error": payload.get("error", "Stripe authentication failed")}
    key = secret_key or _key()
    return {
        "ok": True,
        "status": 200,
        "connected": True,
        "mode": "test" if key.startswith("sk_test_") else "live",
        "account_id": str(payload.get("id", "")),
        "country": str(payload.get("country", "")),
    }


def status() -> dict[str, object]:
    key = _key()
    if not key:
        return {"ok": True, "status": 200, "connected": False, "mode": "disconnected", "webhook_configured": bool(_webhook_secret())}
    result = test_connection(key)
    if not result["ok"]:
        return {"ok": True, "status": 200, "connected": False, "mode": "invalid", "error": result.get("error")}
    result["webhook_configured"] = bool(_webhook_secret())
    return result


def verify_stripe_signature(raw_body: bytes, signature: str | None, secret: str | None = None, now: int | None = None) -> bool:
    if not isinstance(raw_body, (bytes, bytearray)) or not signature:
        return False
    secret = secret or _webhook_secret()
    if not secret:
        return False
    timestamp = None
    signatures = []
    for item in str(signature).split(","):
        key, _, value = item.partition("=")
        if key == "t" and value.isdigit():
            timestamp = int(value)
        elif key == "v1" and value:
            signatures.append(value)
    current = int(time.time() if now is None else now)
    if timestamp is None or abs(current - timestamp) > SIGNATURE_TOLERANCE_SECONDS or not signatures:
        return False
    signed = f"{timestamp}.".encode("utf-8") + bytes(raw_body)
    expected = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, candidate) for candidate in signatures)


def _parse_json(raw_body: bytes) -> dict | None:
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return None
    return payload if isinstance(payload, dict) else None


def _stripe_amount_to_decimal(amount_total: object) -> Decimal | None:
    try:
        minor = int(amount_total)
    except (TypeError, ValueError):
        return None
    if minor <= 0:
        return None
    return (Decimal(minor) / Decimal("100")).quantize(Decimal("0.01"))


def process_stripe_webhook(raw_body: bytes, signature: str | None, secret: str | None = None) -> dict[str, object]:
    if not verify_stripe_signature(raw_body, signature, secret):
        return {"ok": False, "status": 401, "error": "invalid Stripe signature"}
    event = _parse_json(raw_body)
    if event is None:
        return {"ok": False, "status": 400, "error": "invalid JSON payload"}
    if str(event.get("type", "")) != "checkout.session.completed":
        return {"ok": True, "status": 200, "ignored": True, "event_id": str(event.get("id", ""))}
    obj = event.get("data", {}).get("object", {}) if isinstance(event.get("data"), dict) else {}
    if not isinstance(obj, dict) or str(obj.get("payment_status", "")) != "paid":
        return {"ok": True, "status": 200, "ignored": True, "reason": "checkout session is not paid"}
    metadata = obj.get("metadata") if isinstance(obj.get("metadata"), dict) else {}
    order_id = str(metadata.get("cortex_order_id", "")).strip()
    currency = str(obj.get("currency", "")).strip().upper()
    amount = _stripe_amount_to_decimal(obj.get("amount_total"))
    event_id = str(event.get("id", "")).strip()
    transaction_id = str(obj.get("payment_intent") or obj.get("id") or "").strip()
    if not all((event_id, order_id, transaction_id, currency)) or amount is None:
        return {"ok": False, "status": 400, "error": "invalid Stripe checkout event"}
    return process_event({
        "event_id": event_id,
        "type": "payment.succeeded",
        "order_id": order_id,
        "transaction_id": transaction_id,
        "amount": str(amount),
        "currency": currency,
    })


def create_checkout_session(order_id: str, amount: str, currency: str, success_url: str, cancel_url: str, product_name: str = "Cortex digital product", customer_email: str | None = None) -> dict[str, object]:
    try:
        decimal_amount = Decimal(str(amount)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return {"ok": False, "status": 400, "error": "invalid order amount"}
    if decimal_amount <= 0:
        return {"ok": False, "status": 400, "error": "invalid order amount"}
    try:
        minor_units = int(decimal_amount * 100)
    except (ValueError, TypeError):
        return {"ok": False, "status": 400, "error": "invalid order amount"}
    fields = {
        "mode": "payment",
        "success_url": str(success_url),
        "cancel_url": str(cancel_url),
        "client_reference_id": str(order_id),
        "line_items[0][price_data][currency]": str(currency).lower(),
        "line_items[0][price_data][product_data][name]": str(product_name)[:200],
        "line_items[0][price_data][unit_amount]": str(minor_units),
        "line_items[0][quantity]": "1",
        "metadata[cortex_order_id]": str(order_id),
    }
    if customer_email:
        fields["customer_email"] = str(customer_email)
    status_code, payload = _stripe_request("checkout/sessions", data=urlencode(fields).encode("utf-8"), method="POST")
    if status_code < 200 or status_code >= 300:
        return {"ok": False, "status": status_code, "error": payload.get("error", "Stripe Checkout creation failed")}
    return {"ok": True, "status": 200, "session_id": payload.get("id", ""), "checkout_url": payload.get("url", "")}
