import unittest
from unittest.mock import patch

from cortex_command_center_routes import dispatch_command_center_route


class FakeCommand:
    def catalog(self):
        return [{"provider_id": "local_ollama", "name": "Ollama"}]

    def selected(self):
        return {"selected": True, "provider_id": "local_ollama", "model": "test-model"}

    def select(self, payload):
        return {"selected": True, **payload}

    def connection_test(self):
        return {"ok": True, "provider_id": "local_ollama", "model": "test-model"}


class RouteTests(unittest.TestCase):
    def test_command_center_snapshot_route(self):
        with patch("cortex_command_center.communication_status", return_value={}), patch(
            "cortex_command_center.recent_messages", return_value=[]
        ):
            status, body = dispatch_command_center_route("GET", "/api/command-center", command=FakeCommand())
        self.assertEqual(status, 200)
        self.assertEqual(body["engine"], "Cortex Command Center")

    def test_selection_route(self):
        status, body = dispatch_command_center_route(
            "POST", "/api/ai/select", payload={"provider_id": "local_ollama", "model": "test-model"}, command=FakeCommand()
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])

    def test_connection_route_rejects_payload(self):
        status, body = dispatch_command_center_route(
            "POST", "/api/ai/test", payload={"api_key": "x"}, command=FakeCommand()
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "unexpected_payload")
        self.assertNotIn("api_key", str(body))

    def test_unknown_route(self):
        status, body = dispatch_command_center_route("GET", "/api/nope", command=FakeCommand())
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "not_found")


if __name__ == "__main__":
    unittest.main()
