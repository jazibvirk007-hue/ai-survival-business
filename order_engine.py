"""Order lifecycle for real, payment-gated digital delivery.

This module deliberately keeps payment verification separate from customer input.
An order becomes paid only after payment_tracker.verify_payment() accepts an
independently confirmed transaction. Delivery is blocked until that state exists.
"""

import json
import os
from datetime import datetime

from payment_tracker import create_payment_request, get_payment, verify_payment

ORDERS_FILE = "orders.json"

ORDER_STATUSES = {
    "payment_pending",
    "paid",
    "delivery_ready",
    "delivered",
    "cancelled",
}


def _now():
    return datetime.now().isoformat()


def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return []
    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (OSError, ValueError, TypeError):
        return []


def save_orders(orders):
    if not isinstance(orders, list):
        raise TypeError("orders must be a list")
    with open(ORDERS_FILE, "w", encoding="utf-8") as file:
        json.dump(orders, file, indent=4, ensure_ascii=False)


def get_order(order_id):
    if not order_id:
        return None
    return next((order for order in load_orders() if order.get("order_id") == order_id), None)


def create_order(order_id, customer, business_name, product_name, amount, currency="USD"):
    """Create one payment-pending order and its matching payment request."""
    order_id = str(order_id or "").strip()
    if not order_id:
        raise ValueError("order_id is required")
    amount = float(amount)
    if amount <= 0:
        raise ValueError("order amount must be greater than zero")
    currency = str(currency or "USD").strip().upper()
    if not currency:
        raise ValueError("currency is required")

    orders = load_orders()
    existing = next((order for order in orders if order.get("order_id") == order_id), None)
    if existing is not None:
        return existing

    order = {
        "order_id": order_id,
        "customer": str(customer or "").strip(),
        "business_name": str(business_name or "").strip(),
        "product": str(product_name or "").strip(),
        "amount": amount,
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
    create_payment_request(order_id, amount, currency)
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
    """Verify payment and atomically move the order into the paid state.

    The provider/human confirmation is represented by ``confirmed=True`` only
    after independent verification. This function also requires the payment
    amount and currency to exactly match the order before changing order state.
    """
    order = get_order(order_id)
    if order is None:
        return False

    if order.get("status") == "delivered":
        return False

    payment = get_payment(order_id)
    if payment is None:
        return False

    try:
        order_amount = float(order.get("amount", 0))
        payment_amount = float(payment.get("amount", 0))
    except (TypeError, ValueError):
        return False

    if order_amount <= 0 or payment_amount <= 0 or order_amount != payment_amount:
        return False

    order_currency = str(order.get("currency", "USD")).strip().upper()
    payment_currency = str(payment.get("currency", "USD")).strip().upper()
    if order_currency != payment_currency:
        return False

    if not verify_payment(order_id, transaction_id, confirmed=confirmed):
        return False

    updated = dict(order)
    updated["status"] = "paid"
    updated["payment_status"] = "paid"
    updated["delivery_status"] = "ready"
    updated["paid_at"] = payment.get("verified_at") or _now()
    return _save_updated_order(updated)


def mark_delivered(order_id, delivery_file):
    """Record delivery only for an independently paid order."""
    order = get_order(order_id)
    if order is None or order.get("payment_status") != "paid":
        return False
    if not delivery_file:
        return False

    updated = dict(order)
    updated["status"] = "delivered"
    updated["delivery_status"] = "delivered"
    updated["delivery_file"] = str(delivery_file)
    updated["delivered_at"] = _now()
    return _save_updated_order(updated)


def pending_orders():
    return [
        order
        for order in load_orders()
        if order.get("status") == "payment_pending"
    ]


def paid_orders():
    return [
        order
        for order in load_orders()
        if order.get("payment_status") == "paid"
    ]
