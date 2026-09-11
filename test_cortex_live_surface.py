import unittest

from cortex_autonomy_runtime import CortexAutonomyRuntime
from cortex_live_surface import build_live_surface, live_surface_status
from cortex_v95_orchestrator import CortexV95Orchestrator


class LiveSurfaceTests(unittest.TestCase):
    def test_surface_uses_shared_runtime(self):
        runtime = CortexAutonomyRuntime(initial_state={"market_researched": True})
        orchestrator = CortexV95Orchestrator(runtime)
        snapshot = build_live_surface(orchestrator, limit=5)
        self.assertEqual(snapshot["engine"], "Cortex Live Surface")
        self.assertTrue(snapshot["runtime"]["persistence"]["restart_safe"])
        self.assertEqual(snapshot["command_center"]["runtime_health"]["status"], "READY")
        self.assertEqual(snapshot["observability"]["cycles"]["status"], "READY")

    def test_invalid_limit_fails_closed(self):
        orchestrator = CortexV95Orchestrator(CortexAutonomyRuntime())
        with self.assertRaises(ValueError):
            build_live_surface(orchestrator, limit=51)

    def test_wrong_orchestrator_type_rejected(self):
        with self.assertRaises(TypeError):
            build_live_surface(object())

    def test_status_is_browser_safe(self):
        status = live_surface_status()
        self.assertTrue(status["shared_runtime"])
        self.assertEqual(status["status"], "READY")
        self.assertEqual(status["truth_policy"], "read-only observation")


if __name__ == "__main__":
    unittest.main()
