import unittest

from cortex_experiments import CortexExperimentEngine, Experiment


class CortexExperimentTests(unittest.TestCase):
    def test_create_and_pending(self):
        engine = CortexExperimentEngine()
        record = engine.create(Experiment("price-test", "Higher price improves profit", "profit", 10, 12))
        self.assertEqual(record["status"], "running")
        self.assertEqual(len(engine.pending()), 1)

    def test_increase_winner(self):
        engine = CortexExperimentEngine()
        engine.create(Experiment("conversion", "New offer increases conversion", "conversion", 0.05, 0.07))
        result = engine.evaluate("conversion", 0.08)
        self.assertEqual(result["result"], "winner")
        self.assertEqual(engine.status()["completed"], 1)

    def test_decrease_winner(self):
        engine = CortexExperimentEngine()
        engine.create(Experiment("cac", "New channel lowers CAC", "cac", 50, 35, "decrease"))
        result = engine.evaluate("cac", 30)
        self.assertEqual(result["result"], "winner")

    def test_loser_and_unknown_experiment(self):
        engine = CortexExperimentEngine()
        engine.create(Experiment("margin", "Offer improves margin", "margin", 0.4, 0.5))
        result = engine.evaluate("margin", 0.45)
        self.assertEqual(result["result"], "loser")
        with self.assertRaises(KeyError):
            engine.evaluate("missing", 1)

    def test_validation(self):
        with self.assertRaises(ValueError):
            Experiment("x", "h", "m", 1, 2, "sideways")
        with self.assertRaises(ValueError):
            Experiment("", "h", "m", 1, 2)


if __name__ == "__main__":
    unittest.main()
