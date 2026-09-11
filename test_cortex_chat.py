import unittest
from unittest.mock import Mock

from ai_provider import OpenAICompatibleProvider
from cortex_chat import CortexCEOChat


class TestCortexCEOChat(unittest.TestCase):
    def setUp(self):
        self.provider = Mock(spec=OpenAICompatibleProvider)
        self.provider.generate.return_value = "Current cash is $0. No verified revenue yet."
        self.chat = CortexCEOChat(self.provider)

    def test_build_messages_contains_safe_state(self):
        messages = self.chat.build_messages(
            {
                "cash": 0,
                "revenue": 12.5,
                "customers": 2,
                "api_key": "SECRET",
                "internal_notes": {"secret": "hidden"},
            },
            "What should we do next?",
        )
        joined = " ".join(item["content"] for item in messages)
        self.assertIn("12.5", joined)
        self.assertNotIn("SECRET", joined)
        self.assertNotIn("internal_notes", joined)

    def test_respond_uses_provider(self):
        answer = self.chat.respond({"cash": 0, "revenue": 0}, "Status?")
        self.assertEqual(answer, "Current cash is $0. No verified revenue yet.")
        self.provider.generate.assert_called_once()

    def test_respond_records_safe_correlated_events(self):
        recorder = Mock()
        chat = CortexCEOChat(self.provider, communication_recorder=recorder)
        answer = chat.respond({"cash": 0}, "Status? SECRET-DO-NOT-LOG")
        self.assertEqual(answer, "Current cash is $0. No verified revenue yet.")
        self.assertEqual(recorder.call_count, 2)
        request = recorder.call_args_list[0]
        response = recorder.call_args_list[1]
        self.assertEqual(request.args[:4], ("user", "cortex-ceo", "chat_request", "CEO chat request received"))
        self.assertEqual(response.args[:4], ("cortex-ceo", "user", "chat_response", "CEO chat response generated"))
        self.assertEqual(request.kwargs["correlation_id"], response.kwargs["correlation_id"])
        self.assertNotIn("SECRET-DO-NOT-LOG", str(request.kwargs))
        self.assertNotIn("SECRET-DO-NOT-LOG", str(response.kwargs))

    def test_communication_failure_does_not_break_chat(self):
        recorder = Mock(side_effect=RuntimeError("store unavailable"))
        chat = CortexCEOChat(self.provider, communication_recorder=recorder)
        self.assertEqual(chat.respond({}, "Status?"), "Current cash is $0. No verified revenue yet.")
        self.assertEqual(recorder.call_count, 2)

    def test_communication_can_be_disabled(self):
        recorder = Mock()
        chat = CortexCEOChat(self.provider, communication_recorder=None)
        self.assertEqual(chat.respond({}, "Status?"), "Current cash is $0. No verified revenue yet.")
        recorder.assert_not_called()

    def test_empty_message_rejected(self):
        with self.assertRaises(ValueError):
            self.chat.respond({}, "   ")

    def test_state_must_be_dict(self):
        with self.assertRaises(TypeError):
            self.chat.respond([], "Hello")

    def test_long_message_rejected(self):
        with self.assertRaises(ValueError):
            self.chat.respond({}, "x" * 4001)

    def test_invalid_provider_rejected(self):
        with self.assertRaises(TypeError):
            CortexCEOChat(object())

    def test_invalid_communication_recorder_rejected(self):
        with self.assertRaises(TypeError):
            CortexCEOChat(self.provider, communication_recorder=object())


if __name__ == "__main__":
    unittest.main()
