import unittest

from cortex_autonomy_runtime import CortexAutonomyRuntime
from cortex_dashboard_live_api import dispatch_dashboard_live
from cortex_v95_orchestrator import CortexV95Orchestrator


class DashboardLiveApiTests(unittest.TestCase):
    def setUp(self):
        runtime = CortexAutonomyRuntime(initial_state={})
        self.orchestrator = CortexV95Orchestrator(runtime)

    def test_live_surface_uses_shared_orchestrator(self):
        status, body = dispatch_dashboard_live(
            "GET", "/api/command-center/live?limit=5", orchestrator=self.orchestrator
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertTrue(body["live"]["runtime"]["history_count"] >= 0)
        self.assertTrue(body["live"]["truth_policy"].startswith("read-only"))

    def test_cycle_route_is_bounded(self):
        status, body = dispatch_dashboard_live(
            "GET", "/api/cycles?limit=3", orchestrator=self.orchestrator
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "READY")
        self.assertLessEqual(body["count"], 3)

    def test_invalid_limit_fails_closed(self):
        status, body = dispatch_dashboard_live(
            "GET", "/api/cycles?limit=0", orchestrator=self.orchestrator
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "invalid_limit")

    def test_oversized_payload_is_rejected(self):
        payload = {str(i): i for i in range(21)}
        status, body = dispatch_dashboard_live(
            "GET", "/api/command-center/live", orchestrator=self.orchestrator, payload=payload
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "payload_too_large")

    def test_unknown_route_is_not_found(self):
        status, body = dispatch_dashboard_live(
            "GET", "/api/unknown", orchestrator=self.orchestrator
        )
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "not_found")


if __name__ == "__main__":
    unittest.main()
