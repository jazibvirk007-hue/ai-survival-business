"""Contract tests for the V12 Command Center voice route boundary."""
from __future__ import annotations

import json
import unittest

from cortex_v95_orchestrator import build_v95_orchestrator
from cortex_voice_api import parse_json_body
from cortex_voice_routes import json_response, voice_command_from_body, voice_status


def _voice():
    from cortex_voice_api import build_voice_ceo
    return build_voice_ceo(build_v95_orchestrator(initial_state={}))


class VoiceRouteTests(unittest.TestCase):
    def test_voice_status_reports_ready_shared_runtime(self):
        payload = voice_status(_voice())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["voice"]["version"], "12.0")
        self.assertTrue(payload["voice"]["shared_runtime"])

    def test_voice_command_routes_transcript_through_real_runtime(self):
        payload = voice_command_from_body(_voice(), json.dumps({"transcript": "status"}).encode())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"]["intent"], "status")
        self.assertFalse(payload["executed"])

    def test_voice_route_rejects_invalid_json(self):
        with self.assertRaises(ValueError):
            voice_command_from_body(_voice(), b"not-json")

    def test_voice_route_rejects_oversized_body(self):
        with self.assertRaises(ValueError):
            parse_json_body(b"x" * 16_385)

    def test_json_response_is_json_bytes(self):
        raw = json_response({"ok": True})
        self.assertEqual(json.loads(raw.decode()), {"ok": True})


if __name__ == "__main__":
    unittest.main()
