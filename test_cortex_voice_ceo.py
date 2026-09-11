import unittest
from unittest.mock import Mock

from cortex_voice_ceo import CortexVoiceCEO


class VoiceCEOTests(unittest.TestCase):
    def setUp(self):
        self.orchestrator = Mock()
        self.orchestrator.observe.return_value = {
            "runtime": {
                "history_count": 4,
                "state": {"current_decision": "research_market"},
                "registered_actions": ["research_market"],
            }
        }
        self.orchestrator.tick.return_value = {
            "cycle": {"cycle_id": "V9-TEST", "executed": False},
            "runtime": {"history_count": 5},
        }
        self.voice = CortexVoiceCEO(self.orchestrator)

    def test_classifies_status(self):
        command = self.voice.classify("  Cortex, what is the business status?  ")
        self.assertEqual(command.intent, "status")
        self.assertFalse(command.execute)

    def test_status_uses_shared_runtime(self):
        result = self.voice.handle_transcript("Give me a business update")
        self.assertTrue(result["ok"])
        self.assertFalse(result["executed"])
        self.orchestrator.observe.assert_called_once()
        self.assertIn("4 recorded cycles", result["response"])

    def test_cycle_is_observation_only(self):
        result = self.voice.handle_transcript("Run one cycle")
        self.assertTrue(result["ok"])
        self.assertFalse(result["executed"])
        self.orchestrator.tick.assert_called_once_with(execute=False)

    def test_unknown_request_never_executes(self):
        result = self.voice.handle_transcript("Send a message to every customer")
        self.assertTrue(result["ok"])
        self.assertFalse(result["executed"])
        self.orchestrator.tick.assert_not_called()

    def test_audio_requires_adapter(self):
        with self.assertRaises(RuntimeError):
            self.voice.handle_audio(b"audio")

    def test_audio_adapter_routes_transcript(self):
        speech = Mock(return_value="status")
        voice = CortexVoiceCEO(self.orchestrator, speech_to_text=speech)
        result = voice.handle_audio(b"audio")
        self.assertTrue(result["ok"])
        speech.assert_called_once_with(b"audio")

    def test_transcript_length_is_bounded(self):
        with self.assertRaises(ValueError):
            self.voice.handle_transcript("x" * 4001)

    def test_status_reports_v12_boundary(self):
        status = self.voice.status()
        self.assertEqual(status["version"], "12.0")
        self.assertTrue(status["shared_runtime"])
        self.assertEqual(status["decision_cycle"], "bounded_and_observation_first")


if __name__ == "__main__":
    unittest.main()
