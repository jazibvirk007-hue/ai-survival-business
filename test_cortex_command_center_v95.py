import unittest

from cortex_autonomy_runtime import CortexAutonomyRuntime
from cortex_command_center_v95 import build_v95_command_snapshot, run_v95_command
from cortex_v95_orchestrator import CortexV95Orchestrator


class CommandCenterV95Tests(unittest.TestCase):
    def setUp(self):
        self.orchestrator = CortexV95Orchestrator(CortexAutonomyRuntime())

    def test_observe_composes_runtime_and_command_center(self):
        result = build_v95_command_snapshot(self.orchestrator)
        self.assertIn("command_center", result)
        self.assertIn("v95", result)
        self.assertEqual(result["v95"]["max_cycles"], 5)
        self.assertIn("runtime", result["v95"])

    def test_observe_is_default_and_does_not_execute(self):
        result = run_v95_command({"action": "observe"}, orchestrator=self.orchestrator)
        self.assertTrue(result["ok"])
        self.assertIn("command_center", result)

    def test_tick_requires_boolean_execute(self):
        result = run_v95_command({"action": "tick", "execute": "yes"}, orchestrator=self.orchestrator)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "execute_must_be_boolean")

    def test_run_is_bounded(self):
        result = run_v95_command({"action": "run", "cycles": 5, "execute": False}, orchestrator=self.orchestrator)
        self.assertTrue(result["ok"])
        self.assertEqual(result["cycles_completed"], 5)

    def test_run_rejects_more_than_five_cycles(self):
        result = run_v95_command({"action": "run", "cycles": 6}, orchestrator=self.orchestrator)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "cycles_must_be_between_1_and_5")

    def test_unknown_command_fails_closed(self):
        result = run_v95_command({"action": "delete_business"}, orchestrator=self.orchestrator)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "unsupported_action")


if __name__ == "__main__":
    unittest.main()
