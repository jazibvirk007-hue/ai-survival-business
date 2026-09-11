import os
import tempfile
import unittest

from cortex_command_center_routes import dispatch_command_center_route
from cortex_scheduler_service import CortexSchedulerService


class _FakeOrchestrator:
    def tick(self, *, execute=False, approval_id=None):
        return {"executed": execute, "approval_id": approval_id}


class CommandCenterSchedulerIntegrationTests(unittest.TestCase):
    def test_scheduler_status_is_exposed_through_command_center_routes(self):
        with tempfile.TemporaryDirectory() as directory:
            service = CortexSchedulerService(orchestrator=_FakeOrchestrator(), state_path=os.path.join(directory, "scheduler.json"))
            code, body = dispatch_command_center_route("GET", "/api/scheduler", scheduler=service)
            self.assertEqual(code, 200)
            self.assertTrue(body["ok"])
            self.assertEqual(body["scheduler"]["status"], "READY")

    def test_scheduler_tick_defaults_to_observation_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            service = CortexSchedulerService(orchestrator=_FakeOrchestrator(), state_path=os.path.join(directory, "scheduler.json"))
            code, body = dispatch_command_center_route("POST", "/api/scheduler/tick", scheduler=service)
            self.assertEqual(code, 200)
            self.assertTrue(body["ok"])
            self.assertFalse(body["result"]["executed"])

    def test_pause_blocks_tick_until_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            service = CortexSchedulerService(orchestrator=_FakeOrchestrator(), state_path=os.path.join(directory, "scheduler.json"))
            dispatch_command_center_route("POST", "/api/scheduler/pause", scheduler=service)
            code, body = dispatch_command_center_route("POST", "/api/scheduler/tick", scheduler=service)
            self.assertEqual(code, 200)
            self.assertFalse(body["ok"])
            self.assertEqual(body["error"], "scheduler_paused")
            dispatch_command_center_route("POST", "/api/scheduler/resume", scheduler=service)
            code, body = dispatch_command_center_route("POST", "/api/scheduler/tick", scheduler=service)
            self.assertEqual(code, 200)
            self.assertTrue(body["ok"])


if __name__ == "__main__":
    unittest.main()
