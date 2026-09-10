import unittest

from ceo_loop import CEOLoop


class CEOLoopTests(unittest.TestCase):
    def test_decision_only_does_not_execute(self):
        loop = CEOLoop()
        called = []
        loop.register_handler("research_market", lambda state: called.append(state))
        result = loop.cycle({"market_researched": False}, execute=False)
        self.assertEqual(result["decision"]["action"], "research_market")
        self.assertFalse(result["executed"])
        self.assertEqual(called, [])

    def test_safe_handler_executes_once(self):
        loop = CEOLoop()
        called = []
        loop.register_handler("research_market", lambda state: called.append(True) or "researched")
        result = loop.cycle({"market_researched": False}, execute=True)
        self.assertTrue(result["executed"])
        self.assertEqual(result["outcome"], "researched")
        self.assertEqual(len(called), 1)

    def test_approval_required_never_executes(self):
        loop = CEOLoop()
        called = []
        loop.register_handler("follow_up", lambda state: called.append(True))
        state = {
            "market_researched": True,
            "products_available": 1,
            "qualified_prospects": 1,
            "outreach_drafts": 1,
            "approved_outreach": 1,
            "pending_orders": 0,
        }
        result = loop.cycle(state, execute=True)
        self.assertEqual(result["decision"]["action"], "follow_up")
        self.assertEqual(result["outcome"], "approval_required")
        self.assertFalse(result["executed"])
        self.assertEqual(called, [])

    def test_handler_failure_is_recorded(self):
        loop = CEOLoop()
        loop.register_handler("research_market", lambda state: 1 / 0)
        result = loop.cycle({"market_researched": False}, execute=True)
        self.assertFalse(result["executed"])
        self.assertIn("handler_failed: ZeroDivisionError", result["outcome"])

    def test_invalid_registration(self):
        loop = CEOLoop()
        with self.assertRaises(ValueError):
            loop.register_handler("move_money", lambda state: None)
        with self.assertRaises(TypeError):
            loop.register_handler("research_market", None)


if __name__ == "__main__":
    unittest.main()
