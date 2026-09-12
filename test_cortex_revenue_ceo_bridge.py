import os
import tempfile
import unittest
from unittest.mock import patch

import order_engine
import payment_tracker
from ai_ceo import AICEO
from cortex_guard import CortexGuard
from cortex_revenue_ceo_bridge import CortexRevenueCEOBridge
from cortex_revenue_loop import CortexRevenueLoop
from sales_engine import SalesEngine


class CortexRevenueCEOBridgeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.orders = os.path.join(self.directory.name, "orders.json")
        self.payments = os.path.join(self.directory.name, "payments.json")
        self.sales_file = os.path.join(self.directory.name, "sales.json")
        self.guard = CortexGuard(os.path.join(self.directory.name, "approvals.json"))
        self.sales = SalesEngine(self.sales_file)
        self.loop = CortexRevenueLoop(sales=self.sales, guard=self.guard)
        self.bridge = CortexRevenueCEOBridge(revenue_loop=self.loop, ceo=AICEO())
        self.paths = patch.multiple(order_engine, ORDERS_FILE=self.orders), patch.object(payment_tracker, "PAYMENTS_FILE", self.payments)
        self.paths[0].start()
        self.paths[1].start()

    def tearDown(self):
        self.paths[0].stop()
        self.paths[1].stop()
        self.directory.cleanup()

    def test_bridge_injects_factual_revenue_state(self):
        state = self.bridge.observe({"products_available": 1})
        self.assertEqual(state["verified_revenue"], 0.0)
        self.assertEqual(state["orders"], 0)
        self.assertEqual(state["products_available"], 1)

    def test_paid_order_changes_ceo_observation_without_fabricating_revenue(self):
        order_engine.create_order("ORD-BRIDGE", "Customer", "Business", "Agent", 120, "USD")
        before = self.bridge.observe()
        self.assertEqual(before["verified_revenue"], 0.0)
        order_engine.verify_order_payment("ORD-BRIDGE", "txn-bridge", confirmed=True)
        after = self.bridge.observe()
        self.assertEqual(after["verified_revenue"], 120.0)
        self.assertEqual(after["pending_delivery"], 1)

    def test_cycle_is_decision_only_by_default(self):
        result = self.bridge.cycle({"products_available": 1})
        self.assertFalse(result["executed"])
        self.assertEqual(result["outcome"], "decision_only")

    def test_unregistered_action_cannot_execute(self):
        result = self.bridge.cycle({"products_available": 1}, execute=True)
        self.assertFalse(result["executed"])
        self.assertEqual(result["outcome"], "handler_not_registered")

    def test_status_exposes_governance_boundary(self):
        status = self.bridge.status()
        self.assertEqual(status["version"], "13.1")
        self.assertEqual(status["revenue_truth"], "verified_observations_only")


if __name__ == "__main__":
    unittest.main()
