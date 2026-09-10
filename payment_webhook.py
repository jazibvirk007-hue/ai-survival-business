"""Provider-neutral, signature-verified payment webhook adapter.

V7.5 establishes the trust boundary for real payment providers without tying the
business engine to a specific vendor. Providers should translate their webhook
payload into the small canonical event schema accepted here.

Canonical event JSON:
{
    "event_id": "evt_123",
    "type": "payment.succeeded",
    "order_id": "ORD-ABC",
    "transaction_id": "txn_123",
    "amount": 35.0,
    "currency": "USD"
}

Required environment variable:
PAYMENT_WEBHOOK_SECRET

The secret is never stored in source control. Signature format is:
sha256=<hex HMAC-SHA256 of the exact raw request body>
"""

import hashlib
import hmac
import json
import os

from order_engine import get_order, verify_order_payment

WEBHOOK_SECRET_ENV = "PAYMENT_WEBHOOK_SECRET"
EVENTS_FILE = "webhook_events.json"
SUPPORTED_EVENT = "payment.succeeded"


def _load_events():
    if not os.path.exists(EVENTS_FILE):
        return []
    try:
        with open(EVENTS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (OSError, ValueError, TypeError):
        return []


def _save_events(events):
    with open(EVENTS_FILE, "w", encoding="utf-8") as file:
        json.dump(events, file, indent=4, ensure_ascii=False)


def sign_payload(raw_body, secret):
    """Return the canonical HMAC signature for a webhook body."""
    if not isinstance(raw_body, (bytes, bytearray)):
        raise TypeError("raw_body must be bytes")
    if not secret:
        raise ValueError("webhook secret is required")
    digest = hmac.new(secret.encode("utf-8"), bytes(raw_body), hashlib.sha256).hexdigest()
    return "sha256=" + digest


def verify_signature(raw_body, signature, secret=None):
    """Constant-time verify of a provider webhook signature."""
    if not isinstance(raw_body, (bytes, bytearray)) or not signature:
        return False
    secret = secret or os.getenv(WEBHOOK_SECRET_ENV)
    if not secret:
        return False
    expected = sign_payload(raw_body, secret)
    return hmac.compare_digest(expected, str(signature).strip())


def _parse_event(raw_body):
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return None
    return payload if isinstance(payload, dict) else None


def process_webhook(raw_body, signature, secret=None):
    """Authenticate and process one canonical successful-payment event.

    Returns a small result dictionary suitable for an HTTP 200/400/401 response.
    No revenue is created unless the authenticated event matches an existing order
    and its amount/currency/transaction ID pass the order engine's checks.
    """
    if not verify_signature(raw_body, signature, secret):
        return {"ok": False, "status": 401, "error": "invalid signature"}

    event = _parse_event(raw_body)
    if event is None:
        return {"ok": False, "status": 400, "error": "invalid JSON payload"}

    event_id = str(event.get("event_id", "")).strip()
    event_type = str(event.get("type", "")).strip()
    order_id = str(event.get("order_id", "")).strip()
    transaction_id = str(event.get("transaction_id", "")).strip()
    if not all((event_id, order_id, transaction_id)):
        return {"ok": False, "status": 400, "error": "missing event/order/transaction ID"}
    if event_type != SUPPORTED_EVENT:
        return {"ok": False, "status": 400, "error": "unsupported event type"}

    events = _load_events()
    if event_id in events:
        return {"ok": True, "status": 200, "duplicate": True, "event_id": event_id}

    order = get_order(order_id)
    if order is None:
        return {"ok": False, "status": 404, "error": "order not found"}

    try:
        event_amount = float(event.get("amount"))
        order_amount = float(order.get("amount"))
    except (TypeError, ValueError):
        return {"ok": False, "status": 400, "error": "invalid amount"}

    event_currency = str(event.get("currency", "")).strip().upper()
    order_currency = str(order.get("currency", "")).strip().upper()
    if event_amount != order_amount or event_currency != order_currency:
        return {"ok": False, "status": 400, "error": "payment does not match order"}

    if not verify_order_payment(order_id, transaction_id, confirmed=True):
        return {"ok": False, "status": 409, "error": "payment verification rejected"}

    events.append(event_id)
    _save_events(events)
    return {"ok": True, "status": 200, "event_id": event_id, "order_id": order_id}
