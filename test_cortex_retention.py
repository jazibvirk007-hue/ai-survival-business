import unittest

from cortex_retention import CortexRetention, RetentionOpportunity


class CortexRetentionTests(unittest.TestCase):
    def test_customer_metrics(self):
        result = CortexRetention.customer_metrics(100, 25, 40)
        self.assertEqual(result["customers"], 100.0)
        self.assertEqual(result["repeat_customers"], 25.0)
        self.assertAlmostEqual(result["repeat_customer_rate"], 0.25)

    def test_rejects_impossible_repeat_customers(self):
        with self.assertRaises(ValueError):
            CortexRetention.customer_metrics(10, 11)

    def test_rank_prefers_profit_per_effort(self):
        ranked = CortexRetention.rank([
            RetentionOpportunity("slow", "old", "bundle", 100, 20, 0.8, 10, 0.2),
            RetentionOpportunity("fast", "active", "upsell", 80, 10, 0.9, 2, 0.1),
        ])
        self.assertEqual(ranked[0]["name"], "fast")
        self.assertIn("risk_adjusted_profit", ranked[0])

    def test_external_action_is_guarded(self):
        ranked = CortexRetention.rank([
            RetentionOpportunity("winback", "inactive", "offer", 100, 0, 1, 1, 0, True),
        ])
        actions = CortexRetention.next_actions(ranked)
        self.assertEqual(actions[0]["action"], "execute_retention_opportunity")
        self.assertTrue(actions[0]["requires_approval"])

    def test_validation(self):
        with self.assertRaises(ValueError):
            RetentionOpportunity("", "segment", "offer", 10, 1)
        with self.assertRaises(ValueError):
            RetentionOpportunity("x", "segment", "offer", 10, 1, probability=2)


if __name__ == "__main__":
    unittest.main()
