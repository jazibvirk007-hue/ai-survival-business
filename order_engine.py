"""Order lifecycle for real, payment-gated digital delivery."""

import json
import os
import re
import tempfile
from datetime import datetime
from decimal import Decimal, InvalidOperation

from payment_tracker import create_payment_request, delete_payment_request, get_payment, rollback_verified_payment, verify_payment

ORDERS_FILE = "orders.json"
ORDER_STATUSES = {"payment_pending", "paid", "delivery_ready", "delivered", "cancelled"}
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


def _now():
    return datetime.now().isoformat()


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


def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return []
    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, ValueError, TypeError) as error:
        raise RuntimeError("order ledger is unavailable or corrupt") from error
    if not isinstance(data, list):
        raise RuntimeError("order ledger has invalid format")
    return data


def save_orders(orders):
    if not isinstance(orders, list):
        raise TypeError("orders must be a list")
    directory = os.path.dirname(os.path.abspath(ORDERS_FILE))
    fd, temp_path = tempfile.mkstemp(prefix=".orders-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(orders, file, indent=4, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, ORDERS_FILE)
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
            pass


def get_order(order_id):
    if not order_id:
        return None
    return next((order for order in load_orders() if order.get("order_id") == order_id), None)


def create_order(order_id, customer, business_name, product_name, amount, currency="USD"):
    order_id = str(order_id or "").strip()
    if not order_id:
        raise ValueError("order_id is required")
    amount = _money(amount)
    if amount is None:
        raise ValueError("order amount must be greater than zero and valid")
    currency = _currency(currency)
    if currency is None:
        raise ValueError("currency must be a 3-letter code")

    orders = load_orders()
    existing = next((order for order in orders if order.get("order_id") == order_id), None)
    if existing is not None:
        return existing

    order = {
        "order_id": order_id,
        "customer": str(customer or "").strip(),
        "business_name": str(business_name or "").strip(),
        "product": str(product_name or "").strip(),
        "amount": float(amount),
        "currency": currency,
        "status": "payment_pending",
        "payment_status": "unpaid",
        "delivery_status": "not_started",
        "created_at": _now(),
        "paid_at": None,
        "delivered_at": None,
        "delivery_file": None,
    }

    orders.append(order)
    save_orders(orders)
    try:
        create_payment_request(order_id, amount, currency)
    except Exception:
        try:
            delete_payment_request(order_id)
        finally:
            rollback = [item for item in load_orders() if item.get("order_id") != order_id]
            save_orders(rollback)
        raise
    return order


def _save_updated_order(updated):
    orders = load_orders()
    matches = [order for order in orders if order.get("order_id") == updated.get("order_id")]
    if len(matches) != 1:
        return False
    for index, order in enumerate(orders):
        if order.get("order_id") == updated.get("order_id"):
            orders[index] = updated
            save_orders(orders)
            return True
    return False


def verify_order_payment(order_id, transaction_id, confirmed=False):
    order = get_order(order_id)
    if order is None or order.get("status") == "delivered":
        return False

    payment = get_payment(order_id)
    if payment is None:
        return False

    order_amount = _money(order.get("amount"))
    payment_amount = _money(payment.get("amount"))
    if order_amount is None or payment_amount is None or order_amount != payment_amount:
        return False

    order_currency = _currency(order.get("currency"))
    payment_currency = _currency(payment.get("currency"))
    if order_currency is None or payment_currency is None or order_currency != payment_currency:
        return False

    already_verified = payment.get("status") == "verified"
    if not verify_payment(order_id, transaction_id, confirmed=confirmed):
        return False

    updated = dict(order)
    updated["status"] = "paid"
    updated["payment_status"] = "paid"
    updated["delivery_status"] = "ready"
    payment_after = get_payment(order_id)
    updated["paid_at"] = (payment_after or {}).get("verified_at") or _now()
    try:
        return _save_updated_order(updated)
    except Exception:
        if not already_verified:
            try:
                rollback_verified_payment(order_id, transaction_id)
            except Exception as rollback_error:
                raise RuntimeError("order commit failed and payment rollback also failed") from rollback_error
        raise


def mark_delivered(order_id, delivery_file):
    """Record delivery only for an independently paid order and safe relative path."""
    order = get_order(order_id)
    if order is None or order.get("payment_status") != "paid":
        return False
    if not delivery_file:
        return False
    path = os.path.normpath(str(delivery_file).strip())
    if path in ("", ".") or os.path.isabs(path) or path.startswith(".." + os.sep) or path == "..":
        return False
    if not path.startswith("deliveries" + os.sep):
        return False

    updated = dict(order)
    updated["status"] = "delivered"
    updated["delivery_status"] = "delivered"
    updated["delivery_file"] = path
    updated["delivered_at"] = _now()
    return _save_updated_order(updated)


def pending_orders():
    return [order for order in load_orders() if order.get("status") == "payment_pending"]


def paid_orders():
    return [order for order in load_orders() if order.get("payment_status") == "paid"]
