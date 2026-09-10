import os
import tempfile
import unittest

from ceo_loop import CEOLoop
from cortex_guard import CortexGuard


class CEOLoopTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.guard = CortexGuard(os.path.join(self.directory.name, "approvals.json"))
        self.loop = CEOLoop(guard=self.guard)

    def tearDown(self):
        self.directory.cleanup()

    def test_decision_only_does_not_execute(self):
        self.loop.register_handler("research_market", lambda state: "researched")
        result = self.loop.cycle({"market_researched": False}, execute=False)
        self.assertEqual(result["decision"]["action"], "research_market")
        self.assertFalse(result["executed"])
        self.assertEqual(result["outcome"], "decision_only")

    def test_safe_handler_executes_once(self):
        called = []
        self.loop.register_handler("research_market", lambda state: called.append(True) or "researched")
        result = self.loop.cycle({"market_researched": False}, execute=True)
        self.assertTrue(result["executed"])
        self.assertEqual(result["outcome"], "researched")
        self.assertEqual(len(called), 1)

    def _follow_up_state(self):
        return {
            "market_researched": True,
            "products_available": 1,
            "qualified_prospects": 1,
            "outreach_drafts": 1,
            "approved_outreach": 1,
            "pending_orders": 0,
        }

    def test_approval_required_creates_request(self):
        result = self.loop.cycle(self._follow_up_state(), execute=False)
        self.assertEqual(result["decision"]["action"], "follow_up")
        self.assertEqual(result["outcome"], "approval_required")
        self.assertTrue(result["approval_id"])
        self.assertEqual(len(self.guard.pending()), 1)

    def test_approval_required_never_executes_without_id(self):
        called = []
        self.loop.register_handler("follow_up", lambda state: called.append(True))
        result = self.loop.cycle(self._follow_up_state(), execute=True)
        self.assertEqual(result["outcome"], "approval_required")
        self.assertFalse(result["executed"])
        self.assertEqual(called, [])

    def test_approved_action_executes_and_cannot_replay(self):
        first = self.loop.cycle(self._follow_up_state(), execute=False)
        self.guard.approve(first["approval_id"])
        called = []
        self.loop.register_handler("follow_up", lambda state: called.append(state) or "sent")
        executed = self.loop.cycle(self._follow_up_state(), execute=True, approval_id=first["approval_id"])
        self.assertTrue(executed["executed"])
        self.assertEqual(executed["outcome"], "sent")
        self.assertEqual(len(called), 1)
        replay = self.loop.cycle(self._follow_up_state(), execute=True, approval_id=first["approval_id"])
        self.assertFalse(replay["executed"])
        self.assertIn("approval_denied", replay["outcome"])
        self.assertEqual(len(called), 1)

    def test_handler_failure_is_recorded(self):
        self.loop.register_handler("research_market", lambda state: 1 / 0)
        result = self.loop.cycle({"market_researched": False}, execute=True)
        self.assertFalse(result["executed"])
        self.assertIn("handler_failed: ZeroDivisionError", result["outcome"])

    def test_invalid_registration(self):
        with self.assertRaises(ValueError):
            self.loop.register_handler("move_money", lambda state: None)
        with self.assertRaises(TypeError):
            self.loop.register_handler("research_market", None)


if __name__ == "__main__":
    unittest.main()
