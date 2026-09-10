import unittest
from unittest.mock import Mock

from ai_provider import AIProvider
from cortex_chat import CortexCEOChat


class TestCortexCEOChat(unittest.TestCase):
    def setUp(self):
        self.provider = Mock(spec=AIProvider)
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


if __name__ == "__main__":
    unittest.main()
