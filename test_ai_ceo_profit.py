import unittest

from ai_ceo import AICEO


class AICEOProfitTests(unittest.TestCase):
    def test_low_margin_prioritizes_offer_improvement_when_no_blocker(self):
        decision = AICEO().decide({
            "market_researched": True,
            "products_available": 1,
            "verified_revenue": 1000,
            "gross_margin": 0.40,
        })
        self.assertEqual(decision.action, "improve_offer")
        self.assertGreater(decision.priority, 55)

    def test_bad_ltv_to_cac_ratio_prefers_financial_review(self):
        decision = AICEO().decide({
            "market_researched": True,
            "products_available": 1,
            "qualified_prospects": 2,
            "outreach_drafts": 1,
            "pending_orders": 1,
            "verified_revenue": 500,
            "cac": 100,
            "ltv": 200,
        })
        self.assertEqual(decision.action, "review_financials")

    def test_short_runway_gets_cash_preservation_adjustment(self):
        decision = AICEO().decide({
            "market_researched": True,
            "products_available": 1,
            "qualified_prospects": 1,
            "outreach_drafts": 1,
            "approved_outreach": 1,
            "runway_months": 1.5,
        })
        self.assertEqual(decision.action, "follow_up")
        self.assertTrue(decision.requires_approval)

    def test_profit_adjustment_is_bounded(self):
        decision = AICEO().decide({
            "market_researched": True,
            "products_available": 1,
            "verified_revenue": 1000,
            "gross_margin": 0.01,
            "cac": 100,
            "ltv": 101,
            "runway_months": 0.1,
        })
        self.assertGreaterEqual(decision.priority, 0)
        self.assertLessEqual(decision.priority, 100)


if __name__ == "__main__":
    unittest.main()
