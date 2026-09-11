import json
import unittest

from cortex_v95_orchestrator import build_v95_orchestrator
from cortex_voice_api import MAX_BODY_BYTES, handle_voice_payload, parse_json_body
from cortex_voice_ceo import CortexVoiceCEO


class VoiceApiContractTests(unittest.TestCase):
    def setUp(self):
        self.voice = CortexVoiceCEO(build_v95_orchestrator(initial_state={}))

    def test_json_object(self):
        payload = parse_json_body(json.dumps({"transcript": "status"}).encode("utf-8"))
        self.assertEqual(payload["transcript"], "status")

    def test_body_limit(self):
        with self.assertRaises(ValueError):
            parse_json_body(b"x" * (MAX_BODY_BYTES + 1))

    def test_status_routes_to_real_runtime(self):
        result = handle_voice_payload(self.voice, {"transcript": "status"})
        self.assertTrue(result["ok"])
        self.assertFalse(result["executed"])
        self.assertIn("Cortex is online", result["response"])

    def test_unknown_request_is_non_executing(self):
        result = handle_voice_payload(self.voice, {"transcript": "send a customer message"})
        self.assertTrue(result["ok"])
        self.assertFalse(result["executed"])


if __name__ == "__main__":
    unittest.main()
