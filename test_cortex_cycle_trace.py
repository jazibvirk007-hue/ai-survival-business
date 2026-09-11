import unittest

from cortex_cycle_trace import build_cycle_trace


class CycleTraceTests(unittest.TestCase):
    def test_trace_is_observational_and_bounded(self):
        result = {
            "cycle_id": "cycle-1",
            "decision": {"action": "research_market", "priority": 80, "approval_required": False},
            "executed": True,
            "status": "completed",
            "outcome": {"success": True, "summary": "market research completed", "state_patch": {"verified_revenue": 999}},
            "communication_events": [{"id": "1"}, {"id": "2"}],
            "learning_recorded": True,
            "state_changed": True,
            "applied_state_patch": {"market_researched": True, "research_results": ["x"]},
        }
        trace = build_cycle_trace(result)
        self.assertEqual(trace["decision"]["action"], "research_market")
        self.assertEqual(trace["communication"]["events_observed"], 2)
        self.assertEqual(trace["learning"]["recorded"], True)
        self.assertNotIn("verified_revenue", trace["state"]["applied_fields"])
        self.assertIn("verified-only", trace["truth_policy"])

    def test_invalid_result_fails_closed(self):
        with self.assertRaises(TypeError):
            build_cycle_trace(None)


if __name__ == "__main__":
    unittest.main()
