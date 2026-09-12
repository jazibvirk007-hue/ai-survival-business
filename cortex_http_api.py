"""Bounded HTTP API adapters for live observability and payment webhooks.

These adapters contain no execution authority. They translate HTTP inputs into
existing governed Cortex boundaries so the dashboard can expose them without
creating a second business/runtime implementation.
"""
from __future__ import annotations

import json
from typing import Any, Mapping
from urllib.parse import urlparse

from cortex_live_routes import dispatch_live_route
from cortex_lemonsqueezy import translate_webhook
from payment_webhook import process_webhook, process_event

MAX_REQUEST_BYTES = 16_384
PAYMENT_SIGNATURE_HEADERS = ("X-Payment-Signature", "X-Webhook-Signature")
LEMON_SQUEEZY_SIGNATURE_HEADER = "X-Signature"


def _json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(dict(payload), separators=(",", ":")).encode("utf-8")


def dispatch_get(path: str, *, runtime_snapshot: Mapping[str, Any] | None) -> tuple[int, dict[str, Any]] | None:
    """Return an API response for a supported GET route, else ``None``."""
    if urlparse(path).path != "/api/command-center/live":
        return None
    return dispatch_live_route("GET", path, runtime_snapshot=runtime_snapshot)


def dispatch_payment_webhook(raw_body: bytes, signature: str | None) -> tuple[int, dict[str, Any]]:
    """Process the legacy/provider-neutral payment webhook."""
    if not isinstance(raw_body, (bytes, bytearray)):
        return 400, {"ok": False, "error": "invalid request body"}
    if len(raw_body) == 0 or len(raw_body) > MAX_REQUEST_BYTES:
        return 413, {"ok": False, "error": "request too large or empty"}
    result = process_webhook(bytes(raw_body), signature)
    status = result.get("status", 503) if isinstance(result, dict) else 503
    return int(status), result if isinstance(result, dict) else {"ok": False, "error": "webhook unavailable"}


def dispatch_lemonsqueezy_webhook(raw_body: bytes, signature: str | None) -> tuple[int, dict[str, Any]]:
    """Authenticate and normalize a native Lemon Squeezy webhook."""
    if not isinstance(raw_body, (bytes, bytearray)):
        return 400, {"ok": False, "error": "invalid request body"}
    if len(raw_body) == 0 or len(raw_body) > MAX_REQUEST_BYTES:
        return 413, {"ok": False, "error": "request too large or empty"}
    normalized = translate_webhook(bytes(raw_body), signature)
    if not normalized.get("ok"):
        return int(normalized.get("status", 400)), normalized
    if normalized.get("refunded"):
        return 200, normalized
    result = process_event({
        "event_id": normalized["event_id"],
        "type": normalized["event_type"],
        "order_id": normalized["order_id"],
        "transaction_id": normalized["transaction_id"],
        "amount": normalized["amount"],
        "currency": normalized["currency"],
    })
    return int(result.get("status", 503)), result


def payment_signature(headers: Any) -> str | None:
    """Read a provider signature without accepting arbitrary body fields."""
    for name in PAYMENT_SIGNATURE_HEADERS:
        value = headers.get(name)
        if value:
            return str(value).strip()
    return None


def lemonsqueezy_signature(headers: Any) -> str | None:
    value = headers.get(LEMON_SQUEEZY_SIGNATURE_HEADER)
    return str(value).strip() if value else None


def build_payment_event(*, event_id: str, order_id: str, transaction_id: str, amount: str, currency: str) -> bytes:
    """Build deterministic sandbox/test event bytes; production providers sign their own payload."""
    return _json_bytes({
        "event_id": event_id,
        "type": "payment.succeeded",
        "order_id": order_id,
        "transaction_id": transaction_id,
        "amount": amount,
        "currency": currency,
    })
