import unittest

from cortex_live_control import dispatch_live_control, live_control_status
from cortex_scheduler_service import CortexSchedulerService


class FakeOrchestrator:
    def tick(self, *, execute=False, approval_id=None):
        return {"executed": bool(execute), "approval_id": approval_id}


class FakeScheduler:
    def snapshot(self):
        return {"engine": "fake", "paused": False, "recovery": "healthy"}


class LiveControlTests(unittest.TestCase):
    def test_live_snapshot_exposes_scheduler(self):
        service = CortexSchedulerService(orchestrator=FakeOrchestrator(), state_path="/tmp/cortex-test-scheduler.json")
        status, body = dispatch_live_control("GET", "/api/command-center/live", scheduler=service)
        self.assertEqual(status, 200)
        self.assertIn("scheduler", body["command_center"])

    def test_scheduler_pause_blocks_tick(self):
        service = CortexSchedulerService(orchestrator=FakeOrchestrator(), state_path="/tmp/cortex-test-scheduler-paused.json")
        status, _ = dispatch_live_control("POST", "/api/scheduler/pause", scheduler=service)
        self.assertEqual(status, 200)
        status, body = dispatch_live_control("POST", "/api/scheduler/tick", payload={}, scheduler=service)
        self.assertEqual(status, 200)
        self.assertFalse(body["ok"])
        self.assertEqual(body["error"], "scheduler_paused")

    def test_invalid_payload_is_rejected(self):
        status, body = dispatch_live_control("GET", "/api/command-center/live", payload=[])
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "payload_must_be_object")

    def test_payload_bound_is_enforced(self):
        payload = {str(i): i for i in range(21)}
        status, body = dispatch_live_control("GET", "/api/command-center/live", payload=payload)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "payload_too_large")

    def test_unknown_live_route_is_not_found(self):
        status, body = dispatch_live_control("GET", "/api/unknown")
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "not_found")

    def test_browser_safe_status(self):
        status = live_control_status(FakeScheduler())
        self.assertEqual(status["status"], "READY")
        self.assertEqual(status["max_cycles"], 5)
        self.assertIn("verified financial truth", status["truth_policy"])


if __name__ == "__main__":
    unittest.main()
