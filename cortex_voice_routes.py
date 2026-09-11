"""V12 Voice CEO HTTP route helpers for the local Cortex Command Center.

The route layer is intentionally small: transport parsing and the shared runtime
stay outside the browser, while Voice CEO remains the only command interpreter.
"""
from __future__ import annotations

import json
from typing import Any

from cortex_voice_api import handle_voice_payload, parse_json_body
from cortex_voice_ceo import CortexVoiceCEO


def voice_status(voice: CortexVoiceCEO) -> dict[str, Any]:
    return {"ok": True, "voice": voice.status()}


def voice_command_from_body(voice: CortexVoiceCEO, raw_body: bytes) -> dict[str, Any]:
    payload = parse_json_body(raw_body)
    return handle_voice_payload(voice, payload)


def json_response(payload: Any) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")
