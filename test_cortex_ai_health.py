import unittest

from cortex_ai_health import build_ai_health
from cortex_ai_command import CortexAICommand


class FakeCommand:
    def __init__(self, selected, test):
        self._selected = selected
        self._test = test

    def selected(self):
        return self._selected

    def connection_test(self):
        return self._test


class CortexAIHealthTests(unittest.TestCase):
    def test_not_configured(self):
        result = build_ai_health(FakeCommand({"selected": False}, {"ok": False}))
        self.assertEqual(result["status"], "NOT_CONFIGURED")
        self.assertFalse(result["connected"])

    def test_ready_when_connection_succeeds(self):
        result = build_ai_health(FakeCommand(
            {"selected": True, "provider_id": "google_gemini", "model": "gemini-test"},
            {"ok": True},
        ))
        self.assertEqual(result["status"], "READY")
        self.assertTrue(result["connected"])
        self.assertEqual(result["provider_id"], "google_gemini")

    def test_degraded_when_connection_fails(self):
        result = build_ai_health(FakeCommand(
            {"selected": True, "provider_id": "local_ollama", "model": "test-model"},
            {"ok": False, "error": "provider unavailable"},
        ))
        self.assertEqual(result["status"], "DEGRADED")
        self.assertFalse(result["connected"])


if __name__ == "__main__":
    unittest.main()
