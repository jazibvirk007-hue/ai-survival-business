import unittest
from unittest.mock import Mock

from cortex_command_center_routes import dispatch_command_center_route


class CommandCenterSchedulerRouteTests(unittest.TestCase):
    def setUp(self):
        self.scheduler = Mock()
        self.scheduler.snapshot.return_value = {"status": "READY", "paused": False}
        self.scheduler.pause.return_value = {"status": "PAUSED", "paused": True}
        self.scheduler.resume.return_value = {"status": "READY", "paused": False}
        self.scheduler.tick.return_value = {"ok": True, "scheduler": {"status": "READY"}}

    def test_command_center_exposes_scheduler(self):
        code, body = dispatch_command_center_route(
            "GET", "/api/scheduler", service=None, scheduler=self.scheduler
        )
        self.assertEqual(code, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["scheduler"]["status"], "READY")

    def test_pause_and_resume_are_forwarded(self):
        code, body = dispatch_command_center_route("POST", "/api/scheduler/pause", scheduler=self.scheduler)
        self.assertEqual(code, 200)
        self.scheduler.pause.assert_called_once_with()
        self.assertEqual(body["scheduler"]["status"], "PAUSED")

        code, body = dispatch_command_center_route("POST", "/api/scheduler/resume", scheduler=self.scheduler)
        self.assertEqual(code, 200)
        self.scheduler.resume.assert_called_once_with()
        self.assertEqual(body["scheduler"]["status"], "READY")

    def test_tick_defaults_to_observation(self):
        code, body = dispatch_command_center_route("POST", "/api/scheduler/tick", scheduler=self.scheduler)
        self.assertEqual(code, 200)
        self.scheduler.tick.assert_called_once_with(execute=False, approval_id=None)
        self.assertTrue(body["ok"])

    def test_tick_rejects_non_boolean_execute(self):
        code, body = dispatch_command_center_route(
            "POST", "/api/scheduler/tick", payload={"execute": "yes"}, scheduler=self.scheduler
        )
        self.assertEqual(code, 400)
        self.assertEqual(body["error"], "execute_must_be_boolean")
        self.scheduler.tick.assert_not_called()


if __name__ == "__main__":
    unittest.main()
