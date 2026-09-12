from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cortex_agent_factory import CortexAgentFactory
from cortex_autonomous_runtime import CortexAutonomousRuntime
from cortex_autonomous_growth_loop import AutonomousGrowthLoop
from cortex_guard import CortexGuard
from cortex_learning import CortexLearning
from cortex_memory import CortexMemory
from cortex_revenue_loop import CortexRevenueLoop
from cortex_specialist_registry import CortexSpecialistRegistry


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

    def test_register_rejects_unknown_specialist_action(self) -> None:
        with self.assertRaises(ValueError):
            self.runtime.register("send_money", lambda state: None)

    def test_registered_specialist_is_visible_in_status(self) -> None:
        self.runtime.register("research_market", lambda state: {"success": True})
        status = self.runtime.status()
        self.assertEqual(status["version"], "20.2")
        self.assertIn("research_market", status["specialist_registry"]["registered_actions"])
        self.assertEqual(status["agent_factory"]["hired_agents"], 0)

    def test_hire_agent_creates_and_registers_missing_specialist(self) -> None:
        def handler(state):
            return {"success": True, "agent": "pricing"}

        hired = self.runtime.hire_agent(
            name="Pricing Specialist",
            action="improve_offer",
            purpose="Optimize offer pricing from observed business outcomes",
            reason="Observed workload requires offer optimization capacity",
            handler=handler,
            observed_workload=3,
        )
        self.assertEqual(hired.action, "improve_offer")
        self.assertIsNotNone(self.runtime.specialists.get("improve_offer"))
        self.assertEqual(self.runtime.agent_factory.status()["hired_agents"], 1)

    def test_propose_agent_hire_is_non_executing(self) -> None:
        proposal = self.runtime.propose_agent_hire(
            action="review_financials",
            workload=4,
            reason="Observed financial review backlog",
            proposed_name="Finance Capacity Specialist",
            purpose="Handle bounded financial review workload",
        )
        self.assertEqual(proposal["execution"], "not_authorized")
        self.assertEqual(proposal["request"]["action"], "review_financials")
        self.assertIsNone(self.runtime.specialists.get("review_financials"))

    def test_custom_factory_must_share_runtime_registry(self) -> None:
        with self.assertRaises(ValueError):
            CortexAutonomousRuntime(agent_factory=CortexAgentFactory(CortexSpecialistRegistry()))

    def test_hire_agent_does_not_duplicate_staffed_action(self) -> None:
        self.runtime.register("research_market", lambda state: {"success": True})
        with self.assertRaises(ValueError):
            self.runtime.hire_agent(
                name="Second Research Specialist",
                action="research_market",
                purpose="Duplicate research capacity",
                reason="Duplicate staffing should be rejected",
                handler=lambda state: None,
                observed_workload=5,
            )

    def test_status_declares_control_loop(self) -> None:
        status = self.runtime.status()
        self.assertEqual(status["version"], "20.2")
        self.assertEqual(status["control_loop"], ["observe", "decide", "guard", "execute", "verify", "learn", "repeat"])


if __name__ == "__main__":
    unittest.main()
