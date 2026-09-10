import json
import os
import uuid
from datetime import datetime

ORDERS_FILE = "orders.json"


def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return []

    try:
        with open(ORDERS_FILE, "r") as file:
            return json.load(file)
    except Exception:
        return []


def save_orders(orders):
    with open(ORDERS_FILE, "w") as file:
        json.dump(orders, file, indent=4)


def create_order(customer, product, amount):
    orders = load_orders()

    order = {
        "order_id": "ORD-" + uuid.uuid4().hex[:10].upper(),
        "customer": customer,
        "product": product,
        "amount": float(amount),
        "currency": "USD",
        "status": "payment_pending",
        "payment_status": "unpaid",
        "delivery_status": "not_started",
        "created_at": datetime.utcnow().isoformat(),
        "paid_at": None,
        "delivered_at": None,
        "delivery_file": None
    }

    orders.append(order)
    save_orders(orders)

    return order


def get_order(order_id):
    orders = load_orders()

    for order in orders:
        if order["order_id"] == order_id:
            return order

    return None


def update_order(order_id, **changes):
    orders = load_orders()

    for order in orders:

        if order["order_id"] == order_id:

            for key, value in changes.items():
                if key in order:
                    order[key] = value

            save_orders(orders)
            return order

    return None


def list_orders():
    return load_orders()