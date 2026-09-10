import json
import os
from datetime import datetime

PAYMENTS_FILE = "payments.json"


def load_payments():
    if not os.path.exists(PAYMENTS_FILE):
        return []
    try:
        with open(PAYMENTS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (OSError, ValueError, TypeError):
        return []


def save_payments(payments):
    if not isinstance(payments, list):
        raise TypeError("payments must be a list")
    with open(PAYMENTS_FILE, "w", encoding="utf-8") as file:
        json.dump(payments, file, indent=4, ensure_ascii=False)


def create_payment_request(order_id, amount, currency="USD"):
    if not order_id:
        raise ValueError("order_id is required")
    amount = float(amount)
    if amount <= 0:
        raise ValueError("payment amount must be greater than zero")
    currency = str(currency or "USD").strip().upper()
    if not currency:
        raise ValueError("currency is required")

    payments = load_payments()
    for payment in payments:
        if payment.get("order_id") == order_id:
            return payment

    payment = {
        "order_id": str(order_id),
        "amount": amount,
        "currency": currency,
        "status": "requested",
        "transaction_id": None,
        "created_at": datetime.now().isoformat(),
        "verified_at": None,
    }
    payments.append(payment)
    save_payments(payments)
    return payment


def verify_payment(order_id, transaction_id, confirmed=False):
    """Verify an existing payment only after independent confirmation.

    ``confirmed`` is deliberately explicit so a transaction ID alone can never
    create revenue. In production this flag must be set by a trusted payment
    provider/webhook or a controlled human-verification workflow, not by an
    untrusted customer request.
    """
    if not order_id or not transaction_id or not confirmed:
        return False

    order_id = str(order_id).strip()
    transaction_id = str(transaction_id).strip()
    if not order_id or not transaction_id:
        return False

    payments = load_payments()
    matches = [payment for payment in payments if payment.get("order_id") == order_id]
    if len(matches) != 1:
        # Missing or duplicated order records are unsafe to verify automatically.
        return False

    payment = matches[0]
    if payment.get("status") == "verified":
        # Idempotent only for the exact same transaction.
        return payment.get("transaction_id") == transaction_id

    # A verified transaction reference may never be reused for another order.
    for other in payments:
        if (
            other.get("order_id") != order_id
            and other.get("transaction_id") == transaction_id
            and other.get("status") == "verified"
        ):
            return False

    try:
        amount = float(payment.get("amount", 0))
    except (TypeError, ValueError):
        return False
    if amount <= 0:
        return False

    payment["status"] = "verified"
    payment["transaction_id"] = transaction_id
    payment["verified_at"] = datetime.now().isoformat()
    save_payments(payments)
    return True


def get_payment(order_id):
    return next((p for p in load_payments() if p.get("order_id") == order_id), None)


def verified_revenue():
    total = 0.0
    seen_orders = set()
    for payment in load_payments():
        if payment.get("status") != "verified":
            continue
        order_id = payment.get("order_id")
        if order_id in seen_orders:
            continue
        try:
            amount = float(payment.get("amount", 0))
        except (TypeError, ValueError):
            continue
        if amount > 0:
            total += amount
            seen_orders.add(order_id)
    return total


def pending_payments():
    return [p for p in load_payments() if p.get("status") == "requested"]


def verified_payments():
    payments = []
    seen_orders = set()
    for payment in load_payments():
        if payment.get("status") != "verified":
            continue
        order_id = payment.get("order_id")
        if order_id in seen_orders:
            continue
        seen_orders.add(order_id)
        payments.append(payment)
    return payments
