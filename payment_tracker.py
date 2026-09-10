"""Payment ledger with explicit verification and safe monetary comparisons."""

import json
import os
import re
import tempfile
from datetime import datetime
from decimal import Decimal, InvalidOperation

PAYMENTS_FILE = "payments.json"
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


def _money(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not amount.is_finite() or amount <= 0:
        return None
    return amount.quantize(Decimal("0.01"))


def _currency(value):
    currency = str(value or "USD").strip().upper()
    return currency if CURRENCY_RE.fullmatch(currency) else None


def load_payments():
    if not os.path.exists(PAYMENTS_FILE):
        return []
    try:
        with open(PAYMENTS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, ValueError, TypeError) as error:
        raise RuntimeError("payment ledger is unavailable or corrupt") from error
    if not isinstance(data, list):
        raise RuntimeError("payment ledger has invalid format")
    return data


def save_payments(payments):
    if not isinstance(payments, list):
        raise TypeError("payments must be a list")
    directory = os.path.dirname(os.path.abspath(PAYMENTS_FILE))
    fd, temp_path = tempfile.mkstemp(prefix=".payments-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(payments, file, indent=4, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, PAYMENTS_FILE)
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
            pass


def create_payment_request(order_id, amount, currency="USD"):
    order_id = str(order_id or "").strip()
    if not order_id:
        raise ValueError("order_id is required")
    amount = _money(amount)
    if amount is None:
        raise ValueError("payment amount must be greater than zero and valid")
    currency = _currency(currency)
    if currency is None:
        raise ValueError("currency must be a 3-letter code")

    payments = load_payments()
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
        "verified_at": None,
    }
    payments.append(payment)
    save_payments(payments)
    return payment


def verify_payment(order_id, transaction_id, confirmed=False):
    """Verify an existing payment only after independent confirmation."""
    if not order_id or not transaction_id or not confirmed:
        return False

    order_id = str(order_id).strip()
    transaction_id = str(transaction_id).strip()
    if not order_id or not transaction_id:
        return False

    payments = load_payments()
    matches = [payment for payment in payments if payment.get("order_id") == order_id]
    if len(matches) != 1:
        return False

    payment = matches[0]
    if payment.get("status") == "verified":
        return payment.get("transaction_id") == transaction_id

    for other in payments:
        if (
            other.get("order_id") != order_id
            and other.get("transaction_id") == transaction_id
            and other.get("status") == "verified"
        ):
            return False

    if _money(payment.get("amount")) is None:
        return False

    payment["status"] = "verified"
    payment["transaction_id"] = transaction_id
    payment["verified_at"] = datetime.now().isoformat()
    save_payments(payments)
    return True


def rollback_verified_payment(order_id, transaction_id):
    """Revert only the exact payment newly verified by a failed order transaction."""
    order_id = str(order_id or "").strip()
    transaction_id = str(transaction_id or "").strip()
    if not order_id or not transaction_id:
        return False

    payments = load_payments()
    matches = [payment for payment in payments if payment.get("order_id") == order_id]
    if len(matches) != 1:
        return False
    payment = matches[0]
    if payment.get("status") != "verified" or payment.get("transaction_id") != transaction_id:
        return False

    payment["status"] = "requested"
    payment["transaction_id"] = None
    payment["verified_at"] = None
    save_payments(payments)
    return True


def delete_payment_request(order_id):
    """Delete only an unverified payment request during order-creation compensation."""
    order_id = str(order_id or "").strip()
    if not order_id:
        return False
    payments = load_payments()
    kept = []
    removed = False
    for payment in payments:
        if payment.get("order_id") == order_id and payment.get("status") == "requested":
            removed = True
            continue
        kept.append(payment)
    if removed:
        save_payments(kept)
    return removed


def get_payment(order_id):
    return next((p for p in load_payments() if p.get("order_id") == order_id), None)


def verified_revenue():
    total = Decimal("0.00")
    seen_orders = set()
    for payment in load_payments():
        if payment.get("status") != "verified":
            continue
        order_id = payment.get("order_id")
        if order_id in seen_orders:
            continue
        amount = _money(payment.get("amount"))
        if amount is not None:
            total += amount
            seen_orders.add(order_id)
    return float(total)


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
