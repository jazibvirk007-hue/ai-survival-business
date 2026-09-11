import unittest

from cortex_v95_orchestrator import CortexV95Orchestrator


class V95OrchestratorTests(unittest.TestCase):
    def test_tick_is_bounded_and_returns_runtime(self):
        orchestrator = CortexV95Orchestrator()
        result = orchestrator.tick(execute=False)
        self.assertIn("cycle", result)
        self.assertIn("runtime", result)
        self.assertFalse(result["cycle"]["executed"])

    def test_run_bounded_rejects_more_than_five_cycles(self):
        orchestrator = CortexV95Orchestrator()
        with self.assertRaises(ValueError):
            orchestrator.run_bounded(6)

    def test_run_bounded_returns_real_cycle_records(self):
        orchestrator = CortexV95Orchestrator()
        result = orchestrator.run_bounded(2)
        self.assertEqual(result["cycles_requested"], 2)
        self.assertEqual(result["cycles_completed"], 2)
        self.assertEqual(len(result["results"]), 2)
        self.assertTrue(all("cycle" in row for row in result["results"]))


if __name__ == "__main__":
    unittest.main()
