from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cortex_autonomous_runtime import CortexAutonomousRuntime
from cortex_autonomous_growth_loop import AutonomousGrowthLoop
from cortex_guard import CortexGuard
from cortex_learning import CortexLearning
from cortex_memory import CortexMemory
from cortex_revenue_loop import CortexRevenueLoop


class TestCortexAutonomousRuntime(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.orders = root / "orders.json"
        self.payments = root / "payments.json"
        self.guard_file = root / "guard.json"
        self.memory_file = root / "memory.json"
        self.comms = root / "communications.json"
        self.orders.write_text("[]", encoding="utf-8")
        self.payments.write_text("[]", encoding="utf-8")
        guard = CortexGuard(path=str(self.guard_file))
        learning = CortexLearning(CortexMemory(path=str(self.memory_file)))
        growth = AutonomousGrowthLoop(guard=guard, learning=learning, communication_path=str(self.comms))
        revenue = CortexRevenueLoop(guard=guard)
        self.runtime = CortexAutonomousRuntime(growth=growth, revenue=revenue)

    def test_observe_uses_authoritative_revenue(self) -> None:
        with patch("order_engine.ORDERS_FILE", self.orders), patch("payment_tracker.PAYMENTS_FILE", self.payments):
            state = self.runtime.observe({"market_researched": False})
        self.assertEqual(state["verified_revenue"], 0.0)
        self.assertEqual(state["revenue_snapshot"]["verified_payments"], 0)
        self.assertEqual(state["truth_policy"], "verified_observations_only")

    def test_cycle_is_decision_only_by_default(self) -> None:
        with patch("order_engine.ORDERS_FILE", self.orders), patch("payment_tracker.PAYMENTS_FILE", self.payments):
            result = self.runtime.cycle({"market_researched": False})
        self.assertFalse(result["executed"])
        self.assertEqual(result["transition_budget"], 1)
        self.assertEqual(result["verification"], "provider_authoritative")

    def test_handler_executes_only_one_selected_transition(self) -> None:
        calls = []
        def handler(state):
            calls.append(state)
            return {"success": True, "observed": True}
        with patch("order_engine.ORDERS_FILE", self.orders), patch("payment_tracker.PAYMENTS_FILE", self.payments):
            result = self.runtime.cycle({"market_researched": False}, execute=True, handler=handler)
        self.assertTrue(result["executed"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["transition_budget"], 1)

    def test_status_declares_control_loop(self) -> None:
        status = self.runtime.status()
        self.assertEqual(status["version"], "19.0")
        self.assertEqual(status["control_loop"], ["observe", "decide", "guard", "execute", "verify", "learn", "repeat"])


if __name__ == "__main__":
    unittest.main()
