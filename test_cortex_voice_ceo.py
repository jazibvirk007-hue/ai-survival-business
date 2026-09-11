import unittest
from unittest.mock import Mock, patch

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
        self.voice = CortexVoiceCEO.__new__(CortexVoiceCEO)
        self.voice.orchestrator = self.orchestrator
        self.voice.speech_to_text = None
        self.voice.text_to_speech = None
        self.voice.communication_path = "cortex_communications.json"
        self.voice.approval_path = "test-cortex-approvals.json"

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

    def test_pause_creates_guard_proposal_without_execution(self):
        approval = {"id": "approval-123", "status": "pending"}
        with patch("cortex_voice_ceo.CortexGuard.request", return_value=approval) as request:
            result = self.voice.handle_transcript("pause cortex")
        self.assertTrue(result["ok"])
        self.assertFalse(result["executed"])
        self.assertTrue(result["requires_approval"])
        self.assertEqual(result["requested_action"], "scheduler.pause")
        self.assertEqual(result["approval_id"], "approval-123")
        request.assert_called_once()

    def test_resume_creates_guard_proposal_without_execution(self):
        approval = {"id": "approval-456", "status": "pending"}
        with patch("cortex_voice_ceo.CortexGuard.request", return_value=approval):
            result = self.voice.handle_transcript("resume cortex")
        self.assertTrue(result["ok"])
        self.assertFalse(result["executed"])
        self.assertTrue(result["requires_approval"])
        self.assertEqual(result["requested_action"], "scheduler.resume")
        self.assertEqual(result["approval_id"], "approval-456")

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
        voice = CortexVoiceCEO.__new__(CortexVoiceCEO)
        voice.orchestrator = self.orchestrator
        voice.speech_to_text = speech
        voice.text_to_speech = None
        voice.communication_path = "cortex_communications.json"
        voice.approval_path = "test-cortex-approvals.json"
        result = voice.handle_audio(b"audio")
        self.assertTrue(result["ok"])
        speech.assert_called_once_with(b"audio")

    def test_transcript_length_is_bounded(self):
        with self.assertRaises(ValueError):
            self.voice.handle_transcript("x" * 4001)

    def test_voice_telemetry_never_persists_transcript_content(self):
        secret = "DO-NOT-PERSIST-VOICE-SECRET-123"
        with patch("cortex_voice_ceo.record_message") as recorder:
            result = self.voice.handle_transcript(secret)
        self.assertTrue(result["ok"])
        serialized_calls = repr(recorder.call_args_list)
        self.assertNotIn(secret, serialized_calls)
        self.assertEqual(recorder.call_count, 2)
        self.assertIn("transcript_chars", recorder.call_args_list[0].kwargs["metadata"])
        self.assertNotIn("transcript", recorder.call_args_list[0].kwargs["metadata"])

    def test_status_reports_v12_boundary(self):
        status = self.voice.status()
        self.assertEqual(status["version"], "12.0")
        self.assertTrue(status["shared_runtime"])
        self.assertEqual(status["decision_cycle"], "bounded_and_observation_first")
        self.assertEqual(status["control_policy"], "voice requests cannot directly mutate scheduler or external state")


if __name__ == "__main__":
    unittest.main()
