"""Provider-neutral, signature-verified payment webhook adapter."""

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
    except (OSError, ValueError, TypeError):
        # Replay protection must fail closed. Never treat corrupt state as empty.
        raise RuntimeError("webhook event store is unavailable or corrupt")
    if not isinstance(data, list) or any(not isinstance(item, str) or not item for item in data):
        raise RuntimeError("webhook event store has invalid format")
    return data


def _save_events(events):
    if not isinstance(events, list):
        raise TypeError("events must be a list")
    directory = os.path.dirname(os.path.abspath(EVENTS_FILE))
    temp_path = os.path.join(directory, f".{os.path.basename(EVENTS_FILE)}.tmp")
    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(events, file, indent=4, ensure_ascii=False)
        file.flush()
        os.fsync(file.fileno())
    os.replace(temp_path, EVENTS_FILE)


def sign_payload(raw_body, secret):
    if not isinstance(raw_body, (bytes, bytearray)):
        raise TypeError("raw_body must be bytes")
    if not secret:
        raise ValueError("webhook secret is required")
    digest = hmac.new(secret.encode("utf-8"), bytes(raw_body), hashlib.sha256).hexdigest()
    return "sha256=" + digest


def verify_signature(raw_body, signature, secret=None):
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

    try:
        events = _load_events()
    except RuntimeError as error:
        return {"ok": False, "status": 503, "error": str(error)}
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
    if event_amount != order_amount:
        return {"ok": False, "status": 400, "error": "payment does not match order"}

    event_currency = str(event.get("currency", "")).strip().upper()
    order_currency = str(order.get("currency", "")).strip().upper()
    if event_currency != order_currency:
        return {"ok": False, "status": 400, "error": "payment does not match order"}

    if not verify_order_payment(order_id, transaction_id, confirmed=True):
        return {"ok": False, "status": 409, "error": "payment verification rejected"}

    events.append(event_id)
    try:
        _save_events(events)
    except OSError:
        # Payment verification is idempotent for the same transaction; provider retry is safe.
        return {"ok": False, "status": 503, "error": "webhook event store unavailable"}
    return {"ok": True, "status": 200, "event_id": event_id, "order_id": order_id}
