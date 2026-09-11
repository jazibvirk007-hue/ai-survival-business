import unittest

from ai_ceo import AICEO, ACTIONS


class AICEODecisionTests(unittest.TestCase):
    def test_market_research_is_first_when_state_is_empty(self):
        decision = AICEO().decide({})
        self.assertEqual(decision.action, "research_market")
        self.assertIn(decision.action, ACTIONS)

    def test_product_is_next_after_research(self):
        decision = AICEO().decide({"market_researched": True, "products_available": 0})
        self.assertEqual(decision.action, "create_product")

    def test_prospecting_is_next_when_product_exists(self):
        decision = AICEO().decide({"market_researched": True, "products_available": 1, "qualified_prospects": 0})
        self.assertEqual(decision.action, "find_prospects")

    def test_outreach_requires_real_qualified_prospects(self):
        decision = AICEO().decide({"market_researched": True, "products_available": 1, "qualified_prospects": 3, "outreach_drafts": 0})
        self.assertEqual(decision.action, "qualify_prospects")

    def test_approved_outreach_can_trigger_approval_gated_follow_up(self):
        decision = AICEO().decide({"market_researched": True, "products_available": 1, "qualified_prospects": 3, "outreach_drafts": 2, "approved_outreach": 1})
        self.assertEqual(decision.action, "follow_up")
        self.assertTrue(decision.requires_approval)

    def test_pending_orders_do_not_become_revenue(self):
        ceo = AICEO()
        decision = ceo.decide({"market_researched": True, "products_available": 1, "qualified_prospects": 3, "outreach_drafts": 2, "approved_outreach": 1, "pending_orders": 2, "verified_revenue": 0})
        self.assertEqual(decision.action, "review_financials")
        self.assertEqual(ceo.history[-1]["verified_revenue"], 0.0)

    def test_recent_failure_causes_pause(self):
        decision = AICEO().decide({"recent_action_failed": True, "market_researched": True, "products_available": 1})
        self.assertEqual(decision.action, "rest_and_observe")

    def test_stale_market_research_has_priority(self):
        decision = AICEO().decide({"market_researched": True, "market_research_age_hours": 48, "products_available": 1, "qualified_prospects": 10})
        self.assertEqual(decision.action, "research_market")

    def test_invalid_state_and_constructor_are_rejected(self):
        with self.assertRaises(TypeError):
            AICEO().decide([])
        with self.assertRaises(ValueError):
            AICEO(minimum_cash=-1)
        with self.assertRaises(ValueError):
            AICEO(max_actions_per_cycle=0)

    def test_decisions_are_explainable_and_bounded(self):
        ceo = AICEO(max_actions_per_cycle=1)
        decision = ceo.decide({"market_researched": True, "products_available": 1})
        self.assertTrue(decision.reason)
        self.assertTrue(decision.expected_outcome)
        self.assertEqual(ceo.status()["max_actions_per_cycle"], 1)
        self.assertEqual(ceo.status()["execution_policy"], "decision_only; model output and learning cannot authorize actions; irreversible actions require explicit approval")


if __name__ == "__main__":
    unittest.main()
