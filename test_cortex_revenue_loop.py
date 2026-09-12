import os
import tempfile
import unittest
from unittest.mock import patch

import order_engine
import payment_tracker
from cortex_guard import CortexGuard
from cortex_revenue_loop import CortexRevenueLoop
from sales_engine import SalesEngine


class CortexRevenueLoopTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.orders = os.path.join(self.directory.name, "orders.json")
        self.payments = os.path.join(self.directory.name, "payments.json")
        self.approvals = os.path.join(self.directory.name, "approvals.json")
        self.sales_file = os.path.join(self.directory.name, "sales.json")
        self.guard = CortexGuard(self.approvals)
        self.sales = SalesEngine(self.sales_file)
        self.loop = CortexRevenueLoop(sales=self.sales, guard=self.guard)
        self.paths = patch.multiple(
            order_engine, ORDERS_FILE=self.orders,
            payment_tracker, PAYMENTS_FILE=self.payments,
        )
        self.paths.start()

    def tearDown(self):
        self.paths.stop()
        self.directory.cleanup()

    def test_empty_ledger_returns_factual_zero_state(self):
        state = self.loop.observe()
        self.assertEqual(state["orders"], 0)
        self.assertEqual(state["verified_payments"], 0)
        self.assertEqual(state["verified_revenue"], 0.0)
        self.assertEqual(state["truth_policy"], "verified_observations_only")

    def test_empty_ledger_routes_back_to_acquisition(self):
        action = self.loop.next_action()
        self.assertEqual(action["action"], "acquire_next_opportunity")
        self.assertEqual(action["stage"], "Growth")

    def test_unpaid_order_never_becomes_revenue_or_delivery_ready(self):
        order_engine.create_order("ORD-1", "Customer", "Business", "Agent", 100, "USD")
        state = self.loop.observe()
        self.assertEqual(state["pending_orders"], 1)
        self.assertEqual(state["verified_revenue"], 0.0)
        self.assertEqual(state["pending_delivery"], 0)
        self.assertEqual(self.loop.next_action()["action"], "await_payment_confirmation")

    def test_paid_order_becomes_delivery_candidate(self):
        order_engine.create_order("ORD-2", "Customer", "Business", "Agent", 100, "USD")
        self.assertTrue(order_engine.verify_order_payment("ORD-2", "txn-2", confirmed=True))
        state = self.loop.observe()
        self.assertEqual(state["paid_orders"], 1)
        self.assertEqual(state["pending_delivery"], 1)
        self.assertEqual(state["verified_revenue"], 100.0)
        self.assertEqual(self.loop.next_action()["action"], "deliver_paid_order")

    def test_delivery_requires_guard_approval_and_paid_order(self):
        order_engine.create_order("ORD-3", "Customer", "Business", "Agent", 50, "USD")
        denied = self.loop.deliver("ORD-3", "deliveries/agent.zip", "missing")
        self.assertFalse(denied["success"])
        self.assertEqual(denied["error"], "payment_not_verified")

        order_engine.verify_order_payment("ORD-3", "txn-3", confirmed=True)
        request = self.loop.request_delivery("ORD-3")
        self.guard.approve(request["id"])
        delivered = self.loop.deliver("ORD-3", "deliveries/agent.zip", request["id"])
        self.assertTrue(delivered["success"])
        self.assertEqual(order_engine.get_order("ORD-3")["status"], "delivered")

    def test_delivery_approval_is_one_time(self):
        order_engine.create_order("ORD-4", "Customer", "Business", "Agent", 75, "USD")
        order_engine.verify_order_payment("ORD-4", "txn-4", confirmed=True)
        request = self.loop.request_delivery("ORD-4")
        self.guard.approve(request["id"])
        first = self.loop.deliver("ORD-4", "deliveries/agent.zip", request["id"])
        second = self.loop.deliver("ORD-4", "deliveries/agent.zip", request["id"])
        self.assertTrue(first["success"])
        self.assertFalse(second["success"])
        self.assertIn("approval_denied", second["error"])

    def test_status_declares_payment_and_delivery_boundaries(self):
        status = self.loop.status()
        self.assertEqual(status["version"], "13.0")
        self.assertEqual(status["payment_authority"], "independently_confirmed_provider_event")
        self.assertEqual(status["delivery_policy"], "verified_payment_plus_Cortex_Guard")


if __name__ == "__main__":
    unittest.main()
