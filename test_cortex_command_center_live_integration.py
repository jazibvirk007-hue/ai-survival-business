import os
import tempfile
import unittest

from cortex_autonomy_runtime import CortexAutonomyRuntime
from cortex_command_center_routes import dispatch_command_center_route
from cortex_v95_orchestrator import CortexV95Orchestrator
from cortex_scheduler_service import CortexSchedulerService


class CommandCenterLiveIntegrationTests(unittest.TestCase):
    def test_live_surface_uses_the_same_runtime_as_scheduler(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = CortexAutonomyRuntime(
                initial_state={},
                state_path=os.path.join(directory, "runtime.json"),
            )
            orchestrator = CortexV95Orchestrator(runtime)
            scheduler = CortexSchedulerService(
                orchestrator=orchestrator,
                state_path=os.path.join(directory, "scheduler.json"),
            )

            status, body = dispatch_command_center_route(
                "GET",
                "/api/command-center/live?limit=5",
                scheduler=scheduler,
            )
            self.assertEqual(status, 200)
            self.assertTrue(body["ok"])
            self.assertEqual(body["live"]["runtime"]["history_count"], runtime.snapshot()["history_count"])
            self.assertEqual(body["live"]["truth_policy"], "read-only observation; execution remains behind governed scheduler and Guard")

            status, body = dispatch_command_center_route(
                "GET",
                "/api/cycles?limit=5",
                scheduler=scheduler,
            )
            self.assertEqual(status, 200)
            self.assertTrue(body["ok"])
            self.assertEqual(body["count"], 0)

    def test_live_surface_can_use_explicit_orchestrator(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = CortexAutonomyRuntime(
                initial_state={},
                state_path=os.path.join(directory, "runtime.json"),
            )
            orchestrator = CortexV95Orchestrator(runtime)

            status, body = dispatch_command_center_route(
                "GET",
                "/api/command-center/live",
                orchestrator=orchestrator,
            )
            self.assertEqual(status, 200)
            self.assertTrue(body["ok"])
            self.assertEqual(body["live"]["runtime"]["persistence"]["restart_safe"], True)

    def test_live_route_rejects_invalid_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = CortexAutonomyRuntime(
                initial_state={},
                state_path=os.path.join(directory, "runtime.json"),
            )
            orchestrator = CortexV95Orchestrator(runtime)
            status, body = dispatch_command_center_route(
                "GET",
                "/api/command-center/live?limit=51",
                orchestrator=orchestrator,
            )
            self.assertEqual(status, 400)
            self.assertEqual(body["error"], "invalid_limit")


if __name__ == "__main__":
    unittest.main()
