"""HTTP-neutral adapter for the V12 Cortex Voice CEO layer.

The transport accepts either a normalized transcript or an audio payload handled
by an injected speech-to-text adapter. It deliberately contains no credentials
and never enables external execution by itself.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Optional

from cortex_v95_orchestrator import CortexV95Orchestrator
from cortex_voice_ceo import CortexVoiceCEO

MAX_BODY_BYTES = 16_384


def build_voice_ceo(orchestrator: CortexV95Orchestrator, *, speech_to_text: Optional[Callable[[Any], str]] = None, text_to_speech: Optional[Callable[[str], Any]] = None, communication_path: str = "cortex_communications.json") -> CortexVoiceCEO:
    return CortexVoiceCEO(orchestrator, speech_to_text=speech_to_text, text_to_speech=text_to_speech, communication_path=communication_path)


def handle_voice_payload(voice: CortexVoiceCEO, payload: Any) -> dict[str, Any]:
    """Handle a JSON-compatible voice request without exposing transport details."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    if "transcript" in payload:
        return voice.handle_transcript(payload["transcript"])
    if "audio" in payload:
        return voice.handle_audio(payload["audio"])
    raise ValueError("payload requires transcript or audio")


def parse_json_body(raw_body: bytes) -> dict[str, Any]:
    if not isinstance(raw_body, (bytes, bytearray)):
        raise TypeError("raw_body must be bytes")
    if len(raw_body) > MAX_BODY_BYTES:
        raise ValueError("request body is too large")
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid JSON body") from exc
    if not isinstance(payload, dict):
        raise ValueError("JSON body must be an object")
    return payload
