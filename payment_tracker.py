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
    with open(PAYMENTS_FILE, "w", encoding="utf-8") as file:
        json.dump(payments, file, indent=4, ensure_ascii=False)


def create_payment_request(order_id, amount, currency="USD"):
    if not order_id:
        raise ValueError("order_id is required")
    amount = float(amount)
    if amount <= 0:
        raise ValueError("payment amount must be greater than zero")

    payments = load_payments()
    for payment in payments:
        if payment.get("order_id") == order_id:
            return payment

    payment = {
        "order_id": order_id,
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
    """Mark a payment verified only after an independent confirmation.

    The engine never treats a caller-supplied transaction ID as proof by itself.
    A real gateway/webhook or trusted manual verification must set confirmed=True.
    A transaction ID may only be used once across payment records.
    """
    if not order_id or not transaction_id or not confirmed:
        return False

    transaction_id = str(transaction_id).strip()
    if not transaction_id:
        return False

    payments = load_payments()
    for payment in payments:
        if (
            payment.get("transaction_id") == transaction_id
            and payment.get("order_id") != order_id
            and payment.get("status") == "verified"
        ):
            return False

    for payment in payments:
        if payment.get("order_id") == order_id:
            if payment.get("status") == "verified":
                return payment.get("transaction_id") == transaction_id
            payment["status"] = "verified"
            payment["transaction_id"] = transaction_id
            payment["verified_at"] = datetime.now().isoformat()
            save_payments(payments)
            return True
    return False


def get_payment(order_id):
    return next((p for p in load_payments() if p.get("order_id") == order_id), None)


def verified_revenue():
    total = 0.0
    for payment in load_payments():
        if payment.get("status") == "verified":
            try:
                total += float(payment.get("amount", 0))
            except (TypeError, ValueError):
                continue
    return total


def pending_payments():
    return [p for p in load_payments() if p.get("status") == "requested"]


def verified_payments():
    return [p for p in load_payments() if p.get("status") == "verified"]
