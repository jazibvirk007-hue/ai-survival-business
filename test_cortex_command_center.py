import unittest
from unittest.mock import patch

from cortex_command_center import build_command_center_snapshot


class FakeCommand:
    def catalog(self):
        return [{"provider_id": "local_ollama", "name": "Ollama"}]

    def selected(self):
        return {"selected": True, "provider_id": "local_ollama", "model": "test-model"}

    def connection_test(self):
        return {"ok": True, "provider_id": "local_ollama", "model": "test-model"}


class CommandCenterTests(unittest.TestCase):
    def test_snapshot_composes_safe_surfaces(self):
        with patch("cortex_command_center.communication_status", return_value={"events": 3}), patch(
            "cortex_command_center.recent_messages", return_value=[{"from_agent": "CEO", "to_agent": "Growth"}]
        ):
            snapshot = build_command_center_snapshot(command=FakeCommand(), event_limit=10)

        self.assertEqual(snapshot["engine"], "Cortex Command Center")
        self.assertEqual(snapshot["version"], "9.5.2")
        self.assertEqual(snapshot["ai"]["selected"]["provider_id"], "local_ollama")
        self.assertEqual(snapshot["ai"]["health"]["status"], "READY")
        self.assertEqual(len(snapshot["communications"]["events"]), 1)
        self.assertNotIn("api_key", str(snapshot))
        self.assertNotIn("credential_env", snapshot["ai"]["health"])

    def test_event_limit_is_bounded(self):
        seen = {}

        def fake_recent(limit):
            seen["limit"] = limit
            return []

        with patch("cortex_command_center.communication_status", return_value={}), patch(
            "cortex_command_center.recent_messages", side_effect=fake_recent
        ):
            build_command_center_snapshot(command=FakeCommand(), event_limit=999999)

        self.assertEqual(seen["limit"], 50)

    def test_runtime_health_is_optional(self):
        with patch("cortex_command_center.communication_status", return_value={}), patch(
            "cortex_command_center.recent_messages", return_value=[]
        ):
            snapshot = build_command_center_snapshot(command=FakeCommand())
        self.assertIsNone(snapshot["runtime_health"])


if __name__ == "__main__":
    unittest.main()
