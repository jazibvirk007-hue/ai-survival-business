import tempfile
import unittest

from cortex_scheduler_routes import dispatch_scheduler_route
from cortex_scheduler_service import CortexSchedulerService


class StubOrchestrator:
    def __init__(self):
        self.calls = []

    def tick(self, *, execute=False, approval_id=None):
        self.calls.append((execute, approval_id))
        return {"ok": True, "action": "rest_and_observe"}


class SchedulerRoutesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        self.service = CortexSchedulerService(StubOrchestrator(), self.tmp.name)

    def test_status(self):
        code, body = dispatch_scheduler_route("GET", "/api/scheduler", service=self.service)
        self.assertEqual(code, 200)
        self.assertFalse(body["scheduler"]["paused"])

    def test_pause_and_resume(self):
        code, body = dispatch_scheduler_route("POST", "/api/scheduler/pause", service=self.service)
        self.assertEqual(code, 200)
        self.assertTrue(body["scheduler"]["paused"])
        code, body = dispatch_scheduler_route("POST", "/api/scheduler/resume", service=self.service)
        self.assertEqual(code, 200)
        self.assertFalse(body["scheduler"]["paused"])

    def test_tick_defaults_to_non_execute(self):
        code, body = dispatch_scheduler_route("POST", "/api/scheduler/tick", service=self.service)
        self.assertEqual(code, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(self.service.orchestrator.calls[-1], (False, None))

    def test_tick_accepts_approval_id(self):
        code, body = dispatch_scheduler_route(
            "POST", "/api/scheduler/tick", payload={"execute": True, "approval_id": "approval-1"}, service=self.service
        )
        self.assertEqual(code, 200)
        self.assertEqual(self.service.orchestrator.calls[-1], (True, "approval-1"))

    def test_invalid_execute_rejected(self):
        code, body = dispatch_scheduler_route(
            "POST", "/api/scheduler/tick", payload={"execute": "yes"}, service=self.service
        )
        self.assertEqual(code, 400)
        self.assertEqual(body["error"], "execute_must_be_boolean")

    def test_unknown_route(self):
        code, body = dispatch_scheduler_route("GET", "/api/nope", service=self.service)
        self.assertEqual(code, 404)
        self.assertEqual(body["error"], "not_found")


if __name__ == "__main__":
    unittest.main()
