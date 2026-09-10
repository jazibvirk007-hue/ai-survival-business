import json
import os
from datetime import datetime


PAYMENTS_FILE = "payments.json"


def load_payments():

    if not os.path.exists(PAYMENTS_FILE):
        return []

    try:

        with open(
            PAYMENTS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return []


def save_payments(payments):

    with open(
        PAYMENTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            payments,
            file,
            indent=4,
            ensure_ascii=False
        )


def create_payment_request(
    order_id,
    amount,
    currency="USD"
):

    payments = load_payments()

    # Prevent duplicate payment requests
    for payment in payments:

        if payment.get("order_id") == order_id:

            return payment

    payment = {

        "order_id": order_id,

        "amount": float(amount),

        "currency": currency,

        "status": "requested",

        "transaction_id": None,

        "created_at": datetime.now().isoformat(),

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
    Marks a payment as verified ONLY when a real
    transaction ID has been independently confirmed.

    This function does not create or simulate payments.
    """

    if not transaction_id:

        return False

    payments = load_payments()

    for payment in payments:

        if payment.get("order_id") == order_id:

            payment["status"] = "verified"

            payment["transaction_id"] = transaction_id

            payment["verified_at"] = (
                datetime.now().isoformat()
            )

            save_payments(payments)

            return True

    return False


def get_payment(order_id):

    payments = load_payments()

    for payment in payments:

        if payment.get("order_id") == order_id:

            return payment

    return None


def verified_revenue():

    """
    Returns ONLY revenue from payments explicitly
    marked as verified.

    No simulated revenue.
    """

    payments = load_payments()

    total = 0.0

    for payment in payments:

        if payment.get("status") == "verified":

            try:

                total += float(
                    payment.get("amount", 0)
                )

            except (TypeError, ValueError):

                pass

    return total


def pending_payments():

    payments = load_payments()

    return [
        payment
        for payment in payments
        if payment.get("status") == "requested"
    ]


def verified_payments():

    payments = load_payments()

    return [
        payment
        for payment in payments
        if payment.get("status") == "verified"
    ]