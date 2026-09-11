"""V12 voice command boundary for the Cortex Command Center.

This module keeps browser/HTTP concerns outside the CEO command layer. It exposes
small, testable helpers for status/command routing and deliberately does not
perform external outreach, payments, transfers, or other irreversible actions.
"""
from __future__ import annotations

import json
from typing import Any

from cortex_voice_api import handle_voice_payload, parse_json_body

MAX_TRANSCRIPT_CHARS = 4000


def voice_response(payload: Any, voice_ceo: Any) -> dict[str, Any]:
    """Route one already-parsed request through the Voice CEO boundary."""
    return handle_voice_payload(voice_ceo, payload)


def voice_json_response(raw_body: bytes, voice_ceo: Any) -> bytes:
    """Parse and route a JSON request, returning UTF-8 JSON bytes."""
    payload = parse_json_body(raw_body)
    result = voice_response(payload, voice_ceo)
    return json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def voice_endpoint_contract() -> dict[str, Any]:
    """Describe the safe V12 endpoint contract for UI and adapter integration."""
    return {
        "version": "12.0",
        "input": ["transcript", "audio"],
        "max_transcript_chars": MAX_TRANSCRIPT_CHARS,
        "auth": "must inherit the Command Center access boundary",
        "execution": "decision-only unless an explicit approved action is supplied",
        "financial_actions": "blocked-by-default",
        "external_actions": "approval-gated",
        "credentials": "never accepted in payload",
    }
