"""Framework-neutral HTTP route dispatcher for Cortex Command Center.

Returns `(status_code, body)` and leaves HTTP transport concerns to the
existing dashboard server. Responses are bounded JSON-safe dictionaries.
"""

from __future__ import annotations

from typing import Any, Optional

from cortex_ai_command import CortexAICommand
from cortex_command_center import build_command_center_snapshot
from cortex_command_center_actions import select_provider, test_provider

MAX_BODY_KEYS = 20


def _error(code: str) -> tuple[int, dict[str, Any]]:
    return 400, {"ok": False, "error": code}


def dispatch_command_center_route(
    method: str,
    path: str,
    *,
    payload: Optional[dict[str, Any]] = None,
    command: Optional[CortexAICommand] = None,
    runtime_snapshot: Optional[dict[str, Any]] = None,
) -> tuple[int, dict[str, Any]]:
    """Dispatch supported Command Center API routes without exposing secrets."""
    method = str(method).upper()
    payload = payload or {}

    if method == "GET" and path == "/api/command-center":
        return 200, build_command_center_snapshot(command=command, runtime_snapshot=runtime_snapshot)

    if method == "GET" and path == "/api/ai/catalog":
        return 200, {"ok": True, "catalog": (command or CortexAICommand()).catalog()}

    if method == "GET" and path == "/api/ai/selected":
        return 200, {"ok": True, "selected": (command or CortexAICommand()).selected()}

    if method == "POST" and path == "/api/ai/select":
        if len(payload) > MAX_BODY_KEYS:
            return _error("payload_too_large")
        return 200, select_provider(payload, command=command)

    if method == "POST" and path == "/api/ai/test":
        if payload:
            return _error("unexpected_payload")
        return 200, test_provider(command=command)

    return 404, {"ok": False, "error": "not_found"}
