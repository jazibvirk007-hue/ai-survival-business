import unittest

from cortex_v95_orchestrator import build_v95_orchestrator
from cortex_voice_ceo import CortexVoiceCEO


class VoiceCEOIntegrationTests(unittest.TestCase):
    def test_voice_ceo_uses_shared_runtime(self):
        orchestrator = build_v95_orchestrator(initial_state={})
        voice = CortexVoiceCEO(orchestrator)
        result = voice.handle_transcript("Give me a business update")
        self.assertTrue(result["ok"])
        self.assertFalse(result["executed"])
        self.assertIn("runtime", result["observation"])

    def test_voice_cycle_is_decision_only(self):
        orchestrator = build_v95_orchestrator(initial_state={})
        voice = CortexVoiceCEO(orchestrator)
        result = voice.handle_transcript("run one cycle")
        self.assertTrue(result["ok"])
        self.assertFalse(result["executed"])
        self.assertIn("cycle", result)

    def test_voice_status_contract(self):
        orchestrator = build_v95_orchestrator(initial_state={})
        status = CortexVoiceCEO(orchestrator).status()
        self.assertEqual(status["version"], "12.0")
        self.assertEqual(status["execution_authority"], "Cortex scheduler + Guard")
        self.assertEqual(status["truth_policy"], "verified business observations only")


if __name__ == "__main__":
    unittest.main()
