"""Governed live browser control adapter for the Cortex Command Center.

The dashboard receives a narrow command surface over the existing scheduler,
AI control, and Command Center state. It does not gain direct access to ledgers,
credentials, or outbound customer channels.
"""
from __future__ import annotations

from typing import Any, Optional

from cortex_ai_command import CortexAICommand
from cortex_command_center import build_command_center_snapshot
from cortex_command_center_actions import select_provider, test_provider
from cortex_scheduler_routes import dispatch_scheduler_route
from cortex_scheduler_service import CortexSchedulerService

MAX_PAYLOAD_KEYS = 20
MAX_CYCLES = 5
_ALLOWED = frozenset({"observe", "tick", "run", "pause", "resume"})


def dispatch_live_control(
    method: str,
    path: str,
    *,
    payload: Optional[dict[str, Any]] = None,
    command: Optional[CortexAICommand] = None,
    scheduler: Optional[CortexSchedulerService] = None,
) -> tuple[int, dict[str, Any]]:
    """Dispatch browser controls using the existing governance boundaries."""
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        return 400, {"ok": False, "error": "payload_must_be_object"}
    if len(payload) > MAX_PAYLOAD_KEYS:
        return 400, {"ok": False, "error": "payload_too_large"}

    method = method.upper()
    if path.startswith("/api/scheduler"):
        return dispatch_scheduler_route(method, path, payload=payload, service=scheduler)

    command = command or CortexAICommand()
    if method == "GET" and path == "/api/command-center/live":
        scheduler_obj = scheduler or CortexSchedulerService()
        return 200, {
            "ok": True,
            "command_center": build_command_center_snapshot(command=command, scheduler=scheduler_obj),
        }

    if method == "POST" and path == "/api/ai/select":
        return 200, select_provider(payload, command=command)

    if method == "POST" and path == "/api/ai/test":
        if payload:
            return 400, {"ok": False, "error": "unexpected_payload"}
        return 200, test_provider(command=command)

    return 404, {"ok": False, "error": "not_found"}


def live_control_status(scheduler: Optional[CortexSchedulerService] = None) -> dict[str, Any]:
    """Return a browser-safe readiness summary for the live control layer."""
    scheduler_obj = scheduler or CortexSchedulerService()
    scheduler_state = scheduler_obj.snapshot()
    recovery = scheduler_state.get("recovery")
    return {
        "engine": "Cortex Live Control",
        "version": "1.1",
        "status": "DEGRADED" if recovery == "corrupt_state" else "READY",
        "scheduler": scheduler_state,
        "allowed_commands": sorted(_ALLOWED),
        "max_cycles": MAX_CYCLES,
        "truth_policy": "verified financial truth is immutable; external actions remain governed",
    }
