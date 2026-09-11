"""Live browser control adapter for the Cortex Command Center.

This module keeps dashboard controls framework-neutral. It exposes only the
already-governed scheduler and AI provider operations and returns bounded,
JSON-safe state for browser clients.
"""

from __future__ import annotations

from typing import Any, Optional

from cortex_ai_command import CortexAICommand
from cortex_command_center import build_command_center_snapshot
from cortex_command_center_actions import select_provider, test_provider
from cortex_scheduler_routes import dispatch_scheduler_route
from cortex_scheduler_service import CortexSchedulerService

MAX_PAYLOAD_KEYS = 20


def dispatch_live_control(
    method: str,
    path: str,
    *,
    payload: Optional[dict[str, Any]] = None,
    command: Optional[CortexAICommand] = None,
    scheduler: Optional[CortexSchedulerService] = None,
) -> tuple[int, dict[str, Any]]:
    """Dispatch live Command Center controls without granting new authority."""
    payload = payload or {}
    if len(payload) > MAX_PAYLOAD_KEYS:
        return 400, {"ok": False, "error": "payload_too_large"}

    if path.startswith("/api/scheduler"):
        return dispatch_scheduler_route(method, path, payload=payload, service=scheduler)

    command = command or CortexAICommand()
    if method.upper() == "GET" and path == "/api/command-center/live":
        scheduler_obj = scheduler or CortexSchedulerService()
        return 200, {
            "ok": True,
            "command_center": build_command_center_snapshot(command=command, scheduler=scheduler_obj),
        }

    if method.upper() == "POST" and path == "/api/ai/select":
        return 200, select_provider(payload, command=command)

    if method.upper() == "POST" and path == "/api/ai/test":
        if payload:
            return 400, {"ok": False, "error": "unexpected_payload"}
        return 200, test_provider(command=command)

    return 404, {"ok": False, "error": "not_found"}
