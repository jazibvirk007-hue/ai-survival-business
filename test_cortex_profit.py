import unittest

from cortex_profit import CortexProfit, Opportunity


class CortexProfitTests(unittest.TestCase):
    def setUp(self):
        self.engine = CortexProfit()

    def test_unit_economics(self):
        result = self.engine.unit_economics(1000, 300, 10, 200, 5)
        self.assertEqual(result["gross_profit"], 700)
        self.assertAlmostEqual(result["gross_margin"], 0.7)
        self.assertEqual(result["cac"], 20)

    def test_ltv(self):
        self.assertEqual(self.engine.ltv(100, 3, 0.8), 240)

    def test_runway(self):
        self.assertEqual(self.engine.runway_months(1200, 300), 4)
        self.assertIsNone(self.engine.runway_months(1200, 0))

    def test_rank_opportunities(self):
        ranked = self.engine.rank_opportunities([
            Opportunity("A", 100, 20, 0.9, 2, 0.1),
            Opportunity("B", 80, 10, 0.9, 1, 0.1),
        ])
        self.assertEqual(ranked[0]["name"], "B")
        self.assertGreater(ranked[0]["risk_adjusted_profit"], 0)

    def test_anomaly_detection(self):
        anomalies = self.engine.detect_anomalies({"sales": 60, "refunds": 2}, {"sales": 100, "refunds": 2}, 0.3)
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["metric"], "sales")

    def test_zero_baseline_anomaly(self):
        anomalies = self.engine.detect_anomalies({"sales": 1}, {"sales": 0})
        self.assertEqual(anomalies[0]["change_ratio"], None)

    def test_invalid_values_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.ltv(100, 3, 1.1)
        with self.assertRaises(ValueError):
            Opportunity("bad", -1, 0)
        with self.assertRaises(ValueError):
            self.engine.unit_economics(100, 20, 1, gross_margin_target=1)

    def test_recommendations_are_evidence_based(self):
        result = self.engine.recommend({"gross_margin": 0.4, "cac": 50, "ltv": 80, "runway_months": 2})
        self.assertIn("improve gross margin before scaling acquisition", result)
        self.assertIn("improve LTV or reduce CAC before increasing paid acquisition", result)
        self.assertIn("prioritize cash preservation and fast-payback offers", result)


if __name__ == "__main__":
    unittest.main()
