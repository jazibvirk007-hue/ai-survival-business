import unittest

from cortex_goals import CortexGoalEngine, Goal


class CortexGoalEngineTests(unittest.TestCase):
    def test_evaluate_goal_progress(self):
        engine = CortexGoalEngine([Goal("Profit", "verified_profit", 1000, priority=90)])
        result = engine.evaluate({"verified_profit": 250})[0]
        self.assertEqual(result["status"], "in_progress")
        self.assertAlmostEqual(result["progress"], 0.25)
        self.assertEqual(result["gap"], 750)

    def test_achieved_goal(self):
        engine = CortexGoalEngine([Goal("Customers", "customers", 10)])
        result = engine.evaluate({"customers": 12})[0]
        self.assertEqual(result["status"], "achieved")
        self.assertEqual(result["progress"], 1.0)

    def test_unknown_telemetry_does_not_invent_progress(self):
        engine = CortexGoalEngine([Goal("Revenue", "verified_revenue", 100)])
        result = engine.evaluate({})[0]
        self.assertEqual(result["status"], "unknown")
        self.assertIsNone(result["progress"])
        self.assertIsNone(result["gap"])

    def test_next_priority_uses_observed_unmet_goal(self):
        engine = CortexGoalEngine([
            Goal("Revenue", "verified_revenue", 1000, priority=80),
            Goal("Customers", "customers", 10, priority=90),
        ])
        result = engine.next_priority({"verified_revenue": 100, "customers": 2})
        self.assertEqual(result["name"], "Customers")

    def test_validation(self):
        with self.assertRaises(ValueError):
            Goal("", "revenue", 100)
        with self.assertRaises(ValueError):
            Goal("Revenue", "revenue", 100, priority=101)
        with self.assertRaises(TypeError):
            CortexGoalEngine(["not-a-goal"])


if __name__ == "__main__":
    unittest.main()
