import unittest

from cortex_v95_orchestrator import CortexV95Orchestrator
from cortex_v95_routes import dispatch_v95_route


class FakeOrchestrator(CortexV95Orchestrator):
    def __init__(self):
        self.calls = []

    def observe(self):
        self.calls.append(("observe",))
        return {"runtime": {"state": {"observed": True}}, "command_center": {"engine": "Cortex Command Center"}}

    def tick(self, *, execute=False, approval_id=None):
        self.calls.append(("tick", execute, approval_id))
        return {"cycle": {"executed": execute}, "runtime": {"state": {}}}

    def run_bounded(self, cycles=1, *, execute=False):
        self.calls.append(("run", cycles, execute))
        return {"cycles_requested": cycles, "cycles_completed": cycles, "execute": execute}


class V95RouteTests(unittest.TestCase):
    def setUp(self):
        self.orchestrator = FakeOrchestrator()

    def test_observe(self):
        code, body = dispatch_v95_route("GET", "/api/v95/observe", orchestrator=self.orchestrator)
        self.assertEqual(code, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(self.orchestrator.calls, [("observe",)])

    def test_tick_defaults_to_non_execution(self):
        code, body = dispatch_v95_route("POST", "/api/v95/tick", payload={}, orchestrator=self.orchestrator)
        self.assertEqual(code, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(self.orchestrator.calls, [("tick", False, None)])

    def test_tick_passes_explicit_execution_and_approval(self):
        code, _ = dispatch_v95_route("POST", "/api/v95/tick", payload={"execute": True, "approval_id": "A-1"}, orchestrator=self.orchestrator)
        self.assertEqual(code, 200)
        self.assertEqual(self.orchestrator.calls, [("tick", True, "A-1")])

    def test_tick_rejects_invalid_execute(self):
        code, body = dispatch_v95_route("POST", "/api/v95/tick", payload={"execute": "true"}, orchestrator=self.orchestrator)
        self.assertEqual(code, 400)
        self.assertEqual(body["error"], "execute_must_be_boolean")

    def test_run_is_bounded(self):
        code, body = dispatch_v95_route("POST", "/api/v95/run", payload={"cycles": 5}, orchestrator=self.orchestrator)
        self.assertEqual(code, 200)
        self.assertEqual(body["cycles_completed"], 5)

    def test_run_rejects_unbounded_request(self):
        code, body = dispatch_v95_route("POST", "/api/v95/run", payload={"cycles": 6}, orchestrator=self.orchestrator)
        self.assertEqual(code, 400)
        self.assertEqual(body["error"], "cycles_must_be_between_1_and_5")

    def test_unknown_route(self):
        code, body = dispatch_v95_route("GET", "/api/v95/unknown", orchestrator=self.orchestrator)
        self.assertEqual(code, 404)
        self.assertEqual(body["error"], "not_found")


if __name__ == "__main__":
    unittest.main()
