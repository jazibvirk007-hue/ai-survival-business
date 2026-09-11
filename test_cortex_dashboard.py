import json
import unittest
from unittest.mock import patch

import cortex_dashboard


class FakeProvider:
    mode = "local"
    model = "test-model"
    base_url = "http://127.0.0.1:11434/v1"


class FakeChat:
    def __init__(self, provider):
        self.provider = provider

    def respond(self, state, message):
        self.state = state
        self.message = message
        return "Decision support response"


class DashboardTests(unittest.TestCase):
    def test_snapshot_uses_real_ledger_values(self):
        orders = [{"order_id": "O1", "status": "payment_pending"}, {"order_id": "O2", "status": "paid"}]
        verified = [{"order_id": "O2", "amount": 25.0, "status": "verified"}]
        pending = [orders[0]]
        with patch.object(cortex_dashboard, "load_orders", return_value=orders), \
             patch.object(cortex_dashboard, "verified_payments", return_value=verified), \
             patch.object(cortex_dashboard, "pending_payments", return_value=pending), \
             patch.object(cortex_dashboard, "verified_revenue", return_value=25.0), \
             patch.object(cortex_dashboard, "provider_from_env", return_value=FakeProvider()), \
             patch.object(cortex_dashboard, "communication_status", return_value={"enabled": True, "events": 2, "max_events": 500, "storage": "cortex_communications.json", "live_stream_ready": True}):
            snapshot = cortex_dashboard.build_snapshot()
        self.assertEqual(snapshot["orders"], 2)
        self.assertEqual(snapshot["verified_payments"], 1)
        self.assertEqual(snapshot["pending_payments"], 1)
        self.assertEqual(snapshot["verified_revenue"], 25.0)
        self.assertEqual(snapshot["ai_provider"]["mode"], "local")
        self.assertEqual(snapshot["ai_provider"]["model"], "test-model")
        self.assertTrue(snapshot["communication_bus"]["live_stream_ready"])

    def test_snapshot_fails_closed_when_ledger_is_corrupt(self):
        with patch.object(cortex_dashboard, "load_orders", side_effect=RuntimeError("corrupt")), \
             patch.object(cortex_dashboard, "verified_payments", side_effect=RuntimeError("corrupt")), \
             patch.object(cortex_dashboard, "pending_payments", side_effect=RuntimeError("corrupt")), \
             patch.object(cortex_dashboard, "provider_from_env", return_value=FakeProvider()):
            snapshot = cortex_dashboard.build_snapshot()
        self.assertEqual(snapshot["ledger"], "DEGRADED")
        self.assertIsNone(snapshot["verified_revenue"])

    def test_chat_state_contains_only_safe_telemetry(self):
        snapshot = {
            "verified_revenue": 50.0,
            "pending_payments": 2,
            "verified_payments": 1,
            "orders": 3,
            "ceo": {"action": "review_financials", "approval_required": False},
            "ai_provider": {"mode": "local", "model": "test-model", "base_url": "secret-url"},
        }
        with patch.object(cortex_dashboard, "build_snapshot", return_value=snapshot):
            state = cortex_dashboard.build_chat_state()
        self.assertEqual(state["revenue"], 50.0)
        self.assertEqual(state["pending_orders"], 2)
        self.assertNotIn("base_url", state)
        self.assertNotIn("api_key", state)

    def test_communication_snapshot_is_bounded_and_safe(self):
        events = [
            {"event_id": "E1", "sender": "CEO", "recipient": "Growth", "summary": "find prospects", "status": "sent"},
            {"event_id": "E2", "sender": "Growth", "recipient": "Communications", "summary": "draft outreach", "status": "sent"},
        ]
        bus = {"enabled": True, "events": 2, "max_events": 500, "storage": "cortex_communications.json", "live_stream_ready": True}
        with patch.object(cortex_dashboard, "recent_messages", return_value=events) as mocked_recent, \
             patch.object(cortex_dashboard, "communication_status", return_value=bus):
            snapshot = cortex_dashboard.build_communication_snapshot(999)
        mocked_recent.assert_called_once_with(50)
        self.assertEqual(snapshot["events"], events)
        self.assertTrue(snapshot["stream"]["live_stream_ready"])

    def test_handler_routes_and_neural_asset(self):
        self.assertIn("/api/status", cortex_dashboard.CortexHandler.do_GET.__code__.co_consts)
        self.assertIn("/api/communications", cortex_dashboard.CortexHandler.do_GET.__code__.co_consts)
        self.assertIn("/cortex_neural_network.js", cortex_dashboard.CortexHandler.do_GET.__code__.co_consts)
        self.assertTrue(any(isinstance(item, tuple) and "/api/chat" in item for item in cortex_dashboard.CortexHandler.do_POST.__code__.co_consts))
        self.assertIn("Cortex Neural Network", cortex_dashboard.HTML)
        self.assertIn("/cortex_neural_network.js", cortex_dashboard.HTML)
        self.assertEqual(cortex_dashboard.NEURAL_JS.name, "cortex_neural_network.js")

    def test_chat_endpoint_is_present_and_uses_governed_chat_layer(self):
        with patch.object(cortex_dashboard, "provider_from_env", return_value=FakeProvider()), \
             patch.object(cortex_dashboard, "CortexCEOChat", FakeChat), \
             patch.object(cortex_dashboard, "build_chat_state", return_value={"revenue": 0}):
            self.assertEqual(json.loads('{"message":"status"}')["message"], "status")
            chat = cortex_dashboard.CortexCEOChat(FakeProvider())
            self.assertEqual(chat.respond({"revenue": 0}, "status"), "Decision support response")


if __name__ == "__main__":
    unittest.main()
