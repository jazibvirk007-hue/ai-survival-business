"""Governed revenue lifecycle coordinator for Cortex.

This module connects the existing sales, order, payment, delivery and
verified-revenue ledgers without inventing customers, payments or revenue.
It is deliberately observation-first: payment becomes revenue only through
the existing independently-confirmed payment path, and delivery remains
payment-gated.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from cortex_guard import CortexGuard
from order_engine import get_order, load_orders, mark_delivered
from payment_tracker import pending_payments, verified_payments, verified_revenue
from sales_engine import SalesEngine


class CortexRevenueLoop:
    """Observe and safely advance the customer-to-cash lifecycle."""

    def __init__(self, *, sales: Optional[SalesEngine] = None, guard: Optional[CortexGuard] = None) -> None:
        self.sales = sales if sales is not None else SalesEngine()
        self.guard = guard if guard is not None else CortexGuard()
        if not isinstance(self.sales, SalesEngine):
            raise TypeError("sales must be SalesEngine")
        if not isinstance(self.guard, CortexGuard):
            raise TypeError("guard must be CortexGuard")

    def observe(self) -> Dict[str, Any]:
        """Return factual lifecycle counts from the existing ledgers."""
        orders = load_orders()
        if any(not isinstance(item, dict) for item in orders):
            raise RuntimeError("order ledger contains an invalid record")
        sales = self.sales.get_pipeline()
        if any(not isinstance(item, dict) for item in sales):
            raise RuntimeError("sales pipeline contains an invalid record")

        paid = [item for item in orders if item.get("payment_status") == "paid"]
        delivered = [item for item in orders if item.get("status") == "delivered"]
        pending_delivery = [item for item in paid if item.get("status") != "delivered"]
        return {
            "sales_records": len(sales),
            "orders": len(orders),
            "pending_orders": sum(item.get("status") == "payment_pending" for item in orders),
            "pending_payments": len(pending_payments()),
            "paid_orders": len(paid),
            "pending_delivery": len(pending_delivery),
            "delivered_orders": len(delivered),
            "verified_payments": len(verified_payments()),
            "verified_revenue": verified_revenue(),
            "truth_policy": "verified_observations_only",
        }

    def next_action(self) -> Dict[str, Any]:
        """Select one bounded operational action from observed state.

        Payment verification is intentionally not performed here. The
        provider/webhook layer is the authority for independent confirmation.
        """
        state = self.observe()
        if state["pending_payments"] > 0:
            return {"action": "await_payment_confirmation", "stage": "Finance", "reason": "Payment requests exist but no independent confirmation has been observed."}
        if state["pending_delivery"] > 0:
            return {"action": "deliver_paid_order", "stage": "Commerce", "reason": "A paid order is ready for governed delivery."}
        if state["paid_orders"] > 0:
            return {"action": "record_customer_outcome", "stage": "Memory", "reason": "Paid-order outcomes can feed learning after delivery."}
        if state["sales_records"] > 0:
            return {"action": "advance_sales_pipeline", "stage": "Growth", "reason": "Existing sales records need the next evidence-backed transition."}
        return {"action": "acquire_next_opportunity", "stage": "Growth", "reason": "No customer order exists; return to factual opportunity discovery."}

    def request_delivery(self, order_id: str) -> Dict[str, Any]:
        """Create a one-time Guard approval request for paid-order delivery."""
        order = get_order(order_id)
        if order is None:
            raise ValueError("order not found")
        if order.get("payment_status") != "paid":
            raise ValueError("delivery requires independently verified payment")
        if order.get("status") == "delivered":
            raise ValueError("order is already delivered")
        return self.guard.request("deliver_order", f"Deliver paid order {order_id}", 70)

    def deliver(self, order_id: str, delivery_file: str, approval_id: str) -> Dict[str, Any]:
        """Consume Guard approval and record delivery only for a paid order."""
        order = get_order(order_id)
        if order is None:
            return {"success": False, "error": "order_not_found"}
        if order.get("payment_status") != "paid":
            return {"success": False, "error": "payment_not_verified"}
        try:
            approval = self.guard.consume(approval_id, "deliver_order")
        except (KeyError, ValueError) as error:
            return {"success": False, "error": f"approval_denied: {error}"}
        if not mark_delivered(order_id, delivery_file):
            return {"success": False, "error": "delivery_rejected", "approval_id": approval["id"]}
        return {"success": True, "order_id": order_id, "approval_id": approval["id"], "status": "delivered"}

    def status(self) -> Dict[str, Any]:
        return {
            "engine": "Cortex Revenue Loop",
            "version": "13.0",
            "lifecycle": ["discovery", "sales", "order", "payment_confirmation", "delivery", "learning"],
            "payment_authority": "independently_confirmed_provider_event",
            "delivery_policy": "verified_payment_plus_Cortex_Guard",
            "revenue_policy": "verified_observations_only",
            "execution": "one_bounded_transition_at_a_time",
        }
