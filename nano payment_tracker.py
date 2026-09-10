import json
import os
from datetime import datetime

PAYMENTS_FILE = "payments.json"


def load_payments():

    if not os.path.exists(PAYMENTS_FILE):
        return []

    try:
        with open(PAYMENTS_FILE, "r") as file:
            return json.load(file)

    except Exception:
        return []


def save_payments(payments):

    with open(PAYMENTS_FILE, "w") as file:
        json.dump(payments, file, indent=4)


def create_payment_request(
    order_id,
    amount,
    currency="USD"
):

    payments = load_payments()

    payment = {
        "order_id": order_id,
        "amount": float(amount),
        "currency": currency,
        "status": "requested",
        "transaction_id": None,
        "created_at": datetime.utcnow().isoformat(),
        "verified_at": None
    }

    payments.append(payment)
    save_payments(payments)

    return payment


def verify_payment(
    order_id,
    transaction_id
):

    """
    IMPORTANT:

    This function does NOT pretend that a transaction
    exists.

    The transaction must be independently verified
    before this function is called.
    """

    if not transaction_id:
        return False

    payments = load_payments()

    for payment in payments:

        if payment["order_id"] == order_id:

            payment["status"] = "verified"
            payment["transaction_id"] = transaction_id
            payment["verified_at"] = (
                datetime.utcnow().isoformat()
            )

            save_payments(payments)

            return True

    return False


def verified_revenue():

    payments = load_payments()

    total = 0.0

    for payment in payments:

        if payment["status"] == "verified":
            total += payment["amount"]

    return total