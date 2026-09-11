import unittest
from cortex_realtime_test_harness import run_realtime_smoke_test

class RealtimeHarnessTests(unittest.TestCase):
    def test_bounded_local_smoke(self):
        result = run_realtime_smoke_test(2)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["cycles_completed"], 2)
        self.assertTrue(result["invariants"]["financial_truth_unchanged"])
        self.assertTrue(result["invariants"]["financial_patch_blocked"])
        self.assertTrue(result["invariants"]["communication_events_observed"])
        self.assertTrue(result["invariants"]["learning_records_observed"])

    def test_cycle_limit(self):
        with self.assertRaises(ValueError):
            run_realtime_smoke_test(6)

if __name__ == "__main__":
    unittest.main()
