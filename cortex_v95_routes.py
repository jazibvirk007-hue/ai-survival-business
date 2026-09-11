"""Framework-neutral HTTP routes for the V9.5 autonomous runtime."""

from __future__ import annotations

from typing import Any, Optional

from cortex_v95_orchestrator import CortexV95Orchestrator

MAX_CYCLES = 5


def _error(code: str) -> tuple[int, dict[str, Any]]:
    return 400, {"ok": False, "error": code}


def dispatch_v95_route(
    method: str,
    path: str,
    *,
    payload: Optional[dict[str, Any]] = None,
    orchestrator: Optional[CortexV95Orchestrator] = None,
) -> tuple[int, dict[str, Any]]:
    """Expose observation and explicitly requested bounded ticks.

    The route never fabricates state. ``execute=true`` is explicit and external
    actions still require the runtime's existing Cortex Guard approval flow.
    """
    method = str(method).upper()
    payload = payload or {}
    orchestrator = orchestrator or CortexV95Orchestrator()

    if method == "GET" and path == "/api/v95/observe":
        return 200, {"ok": True, **orchestrator.observe()}

    if method == "POST" and path == "/api/v95/tick":
        if len(payload) > 10:
            return _error("payload_too_large")
        execute = payload.get("execute", False)
        if not isinstance(execute, bool):
            return _error("execute_must_be_boolean")
        approval_id = payload.get("approval_id")
        if approval_id is not None and (not isinstance(approval_id, str) or not approval_id.strip() or len(approval_id) > 200):
            return _error("invalid_approval_id")
        return 200, {"ok": True, **orchestrator.tick(execute=execute, approval_id=approval_id)}

    if method == "POST" and path == "/api/v95/run":
        if len(payload) > 10:
            return _error("payload_too_large")
        cycles = payload.get("cycles", 1)
        execute = payload.get("execute", False)
        if not isinstance(cycles, int) or isinstance(cycles, bool) or not 1 <= cycles <= MAX_CYCLES:
            return _error("cycles_must_be_between_1_and_5")
        if not isinstance(execute, bool):
            return _error("execute_must_be_boolean")
        # Bounded planning is safe to batch; execution remains one bounded tick
        # at a time and the runtime still enforces Guard for external actions.
        return 200, {"ok": True, **orchestrator.run_bounded(cycles, execute=execute)}

    return 404, {"ok": False, "error": "not_found"}
