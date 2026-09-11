import unittest

from cortex_live_control import dispatch_live_control
from cortex_scheduler_service import CortexSchedulerService


class FakeOrchestrator:
    def tick(self, *, execute=False, approval_id=None):
        return {"executed": bool(execute), "approval_id": approval_id}


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

    def test_unknown_live_route_is_not_found(self):
        status, body = dispatch_live_control("GET", "/api/unknown")
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "not_found")


if __name__ == "__main__":
    unittest.main()
