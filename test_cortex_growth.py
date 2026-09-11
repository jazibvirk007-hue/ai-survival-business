import unittest

from cortex_growth import CortexGrowth, GrowthOpportunity


class CortexGrowthTests(unittest.TestCase):
    def test_funnel_metrics_use_observed_counts(self):
        result = CortexGrowth.funnel_metrics(100, 20, 10, 4, 200)
        self.assertEqual(result["leads"], 20)
        self.assertAlmostEqual(result["lead_rate"], 0.20)
        self.assertAlmostEqual(result["conversion_rate"], 0.40)
        self.assertAlmostEqual(result["revenue_per_conversion"], 50.0)

    def test_funnel_rejects_impossible_counts(self):
        with self.assertRaises(ValueError):
            CortexGrowth.funnel_metrics(10, 11, 2, 1)

    def test_rank_uses_risk_adjusted_profit_per_effort(self):
        engine = CortexGrowth()
        ranked = engine.rank([
            GrowthOpportunity("slow", "organic", "offer-a", "audience-a", 100, 20, 0.8, 10, 0.2),
            GrowthOpportunity("fast", "direct", "offer-b", "audience-b", 80, 10, 0.9, 2, 0.1),
        ])
        self.assertEqual(ranked[0]["name"], "fast")
        self.assertIn("risk_adjusted_profit", ranked[0])
        self.assertIn("profit_per_effort_hour", ranked[0])

    def test_external_growth_action_is_approval_gated(self):
        ranked = CortexGrowth.rank([
            GrowthOpportunity("outreach", "email", "offer", "qualified leads", 100, 0, 1, 1, 0, True),
        ])
        actions = CortexGrowth.next_actions(ranked)
        self.assertTrue(actions[0]["requires_approval"])
        self.assertEqual(actions[0]["action"], "execute_growth_opportunity")

    def test_validation(self):
        with self.assertRaises(ValueError):
            GrowthOpportunity("", "email", "offer", "audience", 10, 1)
        with self.assertRaises(ValueError):
            GrowthOpportunity("x", "email", "offer", "audience", 10, 1, probability=2)


if __name__ == "__main__":
    unittest.main()
