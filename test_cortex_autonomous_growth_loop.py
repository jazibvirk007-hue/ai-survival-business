import os
import tempfile
import unittest

from cortex_autonomous_growth_loop import AutonomousGrowthLoop
from cortex_guard import CortexGuard
from cortex_learning import CortexLearning
from cortex_memory import CortexMemory
from cortex_communication import recent_messages


class V9AutonomousGrowthLoopTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.guard = CortexGuard(os.path.join(self.directory.name, "approvals.json"))
        self.learning = CortexLearning(CortexMemory(os.path.join(self.directory.name, "memory.json")))
        self.events = os.path.join(self.directory.name, "events.json")
        self.loop = AutonomousGrowthLoop(guard=self.guard, learning=self.learning, communication_path=self.events)

    def tearDown(self):
        self.directory.cleanup()

    def state(self):
        return {
            "market_researched": True,
            "products_available": 1,
            "qualified_prospects": 1,
            "outreach_drafts": 1,
            "approved_outreach": 1,
            "pending_orders": 0,
            "verified_revenue": 0,
        }

    def test_one_cycle_is_bounded_and_emits_handoff(self):
        result = self.loop.cycle({"market_researched": False}, execute=False)
        self.assertEqual(result["stage"], "Intelligence")
        self.assertFalse(result["executed"])
        self.assertEqual(result["outcome"], "decision_only")
        events = recent_messages(path=self.events)
        self.assertTrue(events)
        self.assertEqual(events[0]["sender"], "Cortex CEO")
        self.assertEqual(events[0]["recipient"], "Intelligence")

    def test_external_stage_requires_guard_approval(self):
        self.loop.register("follow_up", lambda state: {"success": True, "sent": True})
        result = self.loop.cycle(self.state(), execute=False)
        self.assertEqual(result["decision"]["action"], "follow_up")
        self.assertEqual(result["outcome"], "approval_required")
        self.assertTrue(result["approval_id"])
        self.assertFalse(result["executed"])

    def test_external_stage_executes_only_with_matching_approval(self):
        calls = []
        self.loop.register("follow_up", lambda state: calls.append(state) or {"success": True})
        request = self.loop.cycle(self.state(), execute=False)
        self.guard.approve(request["approval_id"])
        result = self.loop.cycle(self.state(), execute=True, approval_id=request["approval_id"])
        self.assertTrue(result["executed"])
        self.assertEqual(result["outcome"], {"success": True})
        self.assertEqual(len(calls), 1)

    def test_approval_cannot_be_replayed(self):
        self.loop.register("follow_up", lambda state: "sent")
        request = self.loop.cycle(self.state(), execute=False)
        self.guard.approve(request["approval_id"])
        first = self.loop.cycle(self.state(), execute=True, approval_id=request["approval_id"])
        second = self.loop.cycle(self.state(), execute=True, approval_id=request["approval_id"])
        self.assertTrue(first["executed"])
        self.assertFalse(second["executed"])
        self.assertIn("approval_denied", second["outcome"])

    def test_handler_failure_becomes_learning_signal(self):
        self.loop.register("research_market", lambda state: 1 / 0)
        result = self.loop.cycle({"market_researched": False}, execute=True)
        self.assertFalse(result["executed"])
        self.assertIn("handler_failed", result["outcome"])
        context = self.learning.context(10)
        self.assertTrue(any(item["kind"] == "outcome" and item["metadata"].get("success") is False for item in context))

    def test_status_exposes_v9_pipeline_without_fake_metrics(self):
        status = self.loop.status()
        self.assertEqual(status["version"], "9.2")
        self.assertEqual(status["execution_policy"], "one_bounded_stage_per_cycle")
        self.assertEqual(status["revenue_policy"], "verified_observations_only")
        self.assertIn("Profit", status["pipeline"])


if __name__ == "__main__":
    unittest.main()
