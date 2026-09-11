"""Contract tests for the V12 Command Center voice route boundary."""
from __future__ import annotations

import json

import pytest

from cortex_v95_orchestrator import build_v95_orchestrator
from cortex_voice_api import parse_json_body
from cortex_voice_routes import json_response, voice_command_from_body, voice_status


def _voice():
    from cortex_voice_api import build_voice_ceo
    return build_voice_ceo(build_v95_orchestrator(initial_state={}))


def test_voice_status_reports_ready_shared_runtime():
    payload = voice_status(_voice())
    assert payload["ok"] is True
    assert payload["voice"]["version"] == "12.0"
    assert payload["voice"]["shared_runtime"] is True


def test_voice_command_routes_transcript_through_real_runtime():
    payload = voice_command_from_body(_voice(), json.dumps({"transcript": "status"}).encode())
    assert payload["ok"] is True
    assert payload["command"]["intent"] == "status"
    assert payload["executed"] is False


def test_voice_route_rejects_invalid_json():
    with pytest.raises(ValueError):
        voice_command_from_body(_voice(), b"not-json")


def test_voice_route_rejects_oversized_body():
    with pytest.raises(ValueError):
        parse_json_body(b"x" * 16_385)


def test_json_response_is_json_bytes():
    raw = json_response({"ok": True})
    assert json.loads(raw.decode()) == {"ok": True}
