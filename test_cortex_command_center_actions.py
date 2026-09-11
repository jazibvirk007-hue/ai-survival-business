import unittest
from unittest.mock import Mock

from cortex_command_center_actions import select_provider, test_provider


class CommandCenterActionTests(unittest.TestCase):
    def test_selection_validates_before_command(self):
        command = Mock()
        result = select_provider({"provider_id": "", "model": "x"}, command=command)
        self.assertEqual(result["error"], "provider_required")
        command.select.assert_not_called()

    def test_selection_rejects_oversized_model(self):
        command = Mock()
        result = select_provider({"provider_id": "openai", "model": "x" * 201}, command=command)
        self.assertEqual(result["error"], "model_too_long")
        command.select.assert_not_called()

    def test_selection_delegates_governed_command(self):
        command = Mock()
        command.select.return_value = {"selected": True, "provider_id": "openai", "model": "gpt"}
        result = select_provider({"provider_id": " openai ", "model": " gpt "}, command=command)
        self.assertTrue(result["ok"])
        command.select.assert_called_once_with({"provider_id": "openai", "model": "gpt"})

    def test_connection_test_returns_safe_result(self):
        command = Mock()
        command.connection_test.return_value = {"ok": True, "provider_id": "openai", "model": "gpt"}
        result = test_provider(command=command)
        self.assertEqual(result, {"ok": True, "provider_id": "openai", "model": "gpt", "error": ""})

    def test_connection_test_fail_closed(self):
        command = Mock()
        command.connection_test.side_effect = RuntimeError("secret should not escape")
        result = test_provider(command=command)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "connection_test_failed")
        self.assertNotIn("secret", str(result))


if __name__ == "__main__":
    unittest.main()
