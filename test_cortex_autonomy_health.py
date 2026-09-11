import unittest

from cortex_autonomy_health import evaluate_runtime_health


class CortexAutonomyHealthTests(unittest.TestCase):
    def test_ready_snapshot(self):
        result = evaluate_runtime_health({
            "engine": "Cortex Autonomous Runtime",
            "version": "9.2",
            "registered_actions": ["research_market"],
            "truth_policy": "verified financial observations are immutable here",
            "state": {},
            "history_count": 2,
        })
        self.assertTrue(result["ready"])
        self.assertEqual(result["status"], "READY")

    def test_missing_action_registration_degrades(self):
        result = evaluate_runtime_health({
            "engine": "Cortex Autonomous Runtime",
            "version": "9.2",
            "registered_actions": [],
            "truth_policy": "verified financial observations are immutable here",
            "state": {},
        })
        self.assertFalse(result["ready"])
        self.assertEqual(result["status"], "DEGRADED")

    def test_invalid_snapshot_fails_closed(self):
        result = evaluate_runtime_health(None)
        self.assertFalse(result["ready"])
        self.assertEqual(result["status"], "INVALID_SNAPSHOT")


if __name__ == "__main__":
    unittest.main()
