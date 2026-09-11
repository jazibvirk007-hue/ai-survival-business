import os
import tempfile
import unittest

from cortex_autonomy_runtime import CortexAutonomyRuntime
from cortex_cycle_history_routes import dispatch_cycle_history_route


class CycleHistoryRouteTests(unittest.TestCase):
    def test_history_route_returns_bounded_runtime_history(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = CortexAutonomyRuntime(state_path=os.path.join(directory, "runtime.json"), max_history=3)
            runtime.history = [{"cycle_id": "a", "action": "research_market", "executed": False, "outcome": {"success": None}}, {"cycle_id": "b", "action": "create_product", "executed": False, "outcome": {"success": None}}]
            status, body = dispatch_cycle_history_route("GET", "/api/cycles?limit=2", runtime=runtime)
            self.assertEqual(status, 200)
            self.assertTrue(body["ok"])
            self.assertEqual(body["count"], 2)
            self.assertEqual(body["cycles"][0]["cycle_id"], "b")

    def test_invalid_limit_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = CortexAutonomyRuntime(state_path=os.path.join(directory, "runtime.json"))
            status, body = dispatch_cycle_history_route("GET", "/api/cycles?limit=51", runtime=runtime)
            self.assertEqual(status, 400)
            self.assertEqual(body["error"], "invalid_limit")


if __name__ == "__main__":
    unittest.main()
