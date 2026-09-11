import os
import tempfile
import unittest

from cortex_command_center_routes import dispatch_command_center_route
from cortex_scheduler_service import CortexSchedulerService


class FakeOrchestrator:
    def __init__(self):
        self.calls = []

    def tick(self, *, execute=False, approval_id=None):
        self.calls.append((execute, approval_id))
        return {"ok": True, "executed": bool(execute), "approval_id": approval_id}


class CommandCenterEndToEndTests(unittest.TestCase):
    def test_live_control_path_pause_resume_and_tick(self):
        with tempfile.TemporaryDirectory() as directory:
            service = CortexSchedulerService(
                orchestrator=FakeOrchestrator(),
                state_path=os.path.join(directory, "scheduler.json"),
            )

            status, body = dispatch_command_center_route(
                "GET", "/api/command-center", scheduler=service
            )
            self.assertEqual(status, 200)
            self.assertIn("scheduler", body)
            self.assertFalse(body["scheduler"]["paused"])

            status, body = dispatch_command_center_route(
                "POST", "/api/scheduler/pause", scheduler=service
            )
            self.assertEqual(status, 200)
            self.assertTrue(body["scheduler"]["paused"])

            status, body = dispatch_command_center_route(
                "POST", "/api/scheduler/tick", payload={"execute": True}, scheduler=service
            )
            self.assertEqual(status, 200)
            self.assertFalse(body["ok"])
            self.assertEqual(body["error"], "scheduler_paused")

            status, body = dispatch_command_center_route(
                "POST", "/api/scheduler/resume", scheduler=service
            )
            self.assertEqual(status, 200)
            self.assertFalse(body["scheduler"]["paused"])

            status, body = dispatch_command_center_route(
                "POST",
                "/api/scheduler/tick",
                payload={"execute": False},
                scheduler=service,
            )
            self.assertEqual(status, 200)
            self.assertTrue(body["ok"])
            self.assertEqual(body["scheduler"]["cycles_completed"], 1)
            self.assertEqual(service.orchestrator.calls, [(False, None)])

    def test_execution_requires_explicit_boolean(self):
        with tempfile.TemporaryDirectory() as directory:
            service = CortexSchedulerService(
                orchestrator=FakeOrchestrator(),
                state_path=os.path.join(directory, "scheduler.json"),
            )
            status, body = dispatch_command_center_route(
                "POST",
                "/api/scheduler/tick",
                payload={"execute": "true"},
                scheduler=service,
            )
            self.assertEqual(status, 400)
            self.assertEqual(body["error"], "execute_must_be_boolean")
            self.assertEqual(service.orchestrator.calls, [])


if __name__ == "__main__":
    unittest.main()
