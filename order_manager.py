import json
import os
import uuid
from datetime import datetime

from payment_tracker import create_payment_request, get_payment, verify_payment


class OrderManager:
    """Own the order state machine and keep payment/delivery transitions safe."""

    VALID_STATUSES = {
        "payment_pending",
        "paid",
        "delivered",
        "completed",
        "cancelled",
    }

    def __init__(self, orders_file="orders.json"):
        self.orders_file = orders_file

    def load_orders(self):
        if not os.path.exists(self.orders_file):
            return []
        try:
            with open(self.orders_file, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, list) else []
        except (OSError, ValueError, TypeError):
            return []

    def save_orders(self, orders):
        if not isinstance(orders, list):
            raise TypeError("orders must be a list")
        with open(self.orders_file, "w", encoding="utf-8") as file:
            json.dump(orders, file, indent=4, ensure_ascii=False)

    def get_order(self, order_id):
        return next(
            (order for order in self.load_orders() if order.get("order_id") == str(order_id)),
            None,
        )

    def create_order(self, customer, business_name, product_name, amount, currency="USD"):
        customer = str(customer or "").strip()
        business_name = str(business_name or "").strip()
        product_name = str(product_name or "").strip()
        if not customer or not business_name or not product_name:
            raise ValueError("customer, business_name and product_name are required")

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            raise ValueError("order amount must be a valid number")
        if amount <= 0:
            raise ValueError("order amount must be greater than zero")

        currency = str(currency or "USD").strip().upper()
        if not currency:
            raise ValueError("currency is required")

        order = {
            "order_id": "ORD-" + uuid.uuid4().hex[:10].upper(),
            "customer": customer,
            "business_name": business_name,
            "product": product_name,
            "amount": amount,
            "currency": currency,
            "status": "payment_pending",
            "payment_status": "unpaid",
            "delivery_status": "not_started",
            "created_at": datetime.now().isoformat(),
            "paid_at": None,
            "delivered_at": None,
            "completed_at": None,
            "delivery_file": None,
        }
        orders = self.load_orders()
        orders.append(order)
        self.save_orders(orders)
        create_payment_request(order["order_id"], amount, currency)
        return order

    def confirm_payment(self, order_id, transaction_id, confirmed=False):
        order = self.get_order(order_id)
        if not order:
            return False

        if order.get("status") in {"delivered", "completed"}:
            payment = get_payment(order_id)
            return bool(payment and payment.get("transaction_id") == str(transaction_id).strip())

        payment = get_payment(order_id)
        if not payment or len([p for p in self.load_payment_records() if p.get("order_id") == str(order_id)]) != 1:
            return False

        try:
            order_amount = float(order.get("amount", 0))
            payment_amount = float(payment.get("amount", 0))
        except (TypeError, ValueError):
            return False

        order_currency = str(order.get("currency", "")).strip().upper()
        payment_currency = str(payment.get("currency", "")).strip().upper()
        if order_amount <= 0 or payment_amount != order_amount or payment_currency != order_currency:
            return False

        if not verify_payment(order_id, transaction_id, confirmed=confirmed):
            return False

        order["status"] = "paid"
        order["payment_status"] = "paid"
        order["paid_at"] = datetime.now().isoformat()
        self._replace_order(order)
        return True

    def load_payment_records(self):
        payment_file = "payments.json"
        if not os.path.exists(payment_file):
            return []
        try:
            with open(payment_file, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, list) else []
        except (OSError, ValueError, TypeError):
            return []

    def mark_delivered(self, order_id, delivery_file):
        order = self.get_order(order_id)
        if not order or order.get("payment_status") != "paid":
            return False
        delivery_file = str(delivery_file or "").strip()
        if not delivery_file:
            return False

        if order.get("status") in {"delivered", "completed"}:
            return order.get("delivery_file") == delivery_file

        order["status"] = "delivered"
        order["delivery_status"] = "delivered"
        order["delivery_file"] = delivery_file
        order["delivered_at"] = datetime.now().isoformat()
        self._replace_order(order)
        return True

    def complete_order(self, order_id):
        order = self.get_order(order_id)
        if not order or order.get("payment_status") != "paid":
            return False
        if order.get("status") == "completed":
            return True
        if order.get("status") != "delivered":
            return False

        order["status"] = "completed"
        order["completed_at"] = datetime.now().isoformat()
        self._replace_order(order)
        return True

    def _replace_order(self, updated_order):
        orders = self.load_orders()
        order_id = updated_order.get("order_id")
        replaced = False
        for index, order in enumerate(orders):
            if order.get("order_id") == order_id:
                orders[index] = updated_order
                replaced = True
                break
        if not replaced:
            return False
        self.save_orders(orders)
        return True
