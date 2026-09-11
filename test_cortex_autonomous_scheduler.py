import unittest

from cortex_autonomous_scheduler import CortexAutonomousScheduler
from cortex_autonomy_runtime import CortexAutonomyRuntime
from cortex_v95_orchestrator import CortexV95Orchestrator


class AutonomousSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.scheduler = CortexAutonomousScheduler(
            CortexV95Orchestrator(CortexAutonomyRuntime())
        )

    def test_plans_without_execution_by_default(self):
        decision = self.scheduler.plan()
        self.assertEqual(decision.action, "tick")
        self.assertFalse(decision.execute)

    def test_tick_is_bounded(self):
        result = self.scheduler.tick()
        self.assertTrue(result["ok"])
        self.assertEqual(result["total_ticks"], 1)
        self.assertIn(result["status"], {"RUNNING", "PAUSED"})

    def test_pause_after_repeated_failures(self):
        self.scheduler.max_consecutive_failures = 2
        self.scheduler.orchestrator.runtime.step = lambda **_: {"outcome": {"failed": True}}
        self.scheduler.tick()
        result = self.scheduler.tick()
        self.assertEqual(result["status"], "PAUSED")
        self.assertEqual(result["recovery"], "manual_resume_required")

    def test_paused_scheduler_does_not_tick(self):
        self.scheduler.paused = True
        result = self.scheduler.tick()
        self.assertEqual(result["status"], "PAUSED")
        self.assertEqual(result["decision"]["action"], "pause")

    def test_resume_resets_recovery_state(self):
        self.scheduler.paused = True
        self.scheduler.consecutive_failures = 3
        result = self.scheduler.resume()
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "RUNNING")
        self.assertEqual(self.scheduler.consecutive_failures, 0)


if __name__ == "__main__":
    unittest.main()
