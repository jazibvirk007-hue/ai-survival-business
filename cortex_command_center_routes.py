"""Framework-neutral HTTP route dispatcher for Cortex Command Center."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from cortex_ai_command import CortexAICommand
from cortex_command_center import build_command_center_snapshot
from cortex_command_center_actions import select_provider, test_provider
from cortex_cycle_history_routes import dispatch_cycle_history_route
from cortex_dashboard_live_api import dispatch_dashboard_live
from cortex_runtime_singleton import get_cortex_orchestrator
from cortex_scheduler_routes import dispatch_scheduler_route
from cortex_scheduler_service import CortexSchedulerService

if TYPE_CHECKING:
    from cortex_v95_orchestrator import CortexV95Orchestrator

MAX_BODY_KEYS = 20


def _error(code: str) -> tuple[int, dict[str, Any]]:
    return 400, {"ok": False, "error": code}


def _shared_orchestrator(
    scheduler: Optional[CortexSchedulerService],
    orchestrator: Optional["CortexV95Orchestrator"],
) -> "CortexV95Orchestrator":
    """Resolve one orchestrator so browser reads share the execution authority."""
    if orchestrator is not None:
        return orchestrator
    if scheduler is not None:
        return scheduler.orchestrator
    return get_cortex_orchestrator()


def dispatch_command_center_route(
    method: str,
    path: str,
    *,
    payload: Optional[dict[str, Any]] = None,
    command: Optional[CortexAICommand] = None,
    runtime_snapshot: Optional[dict[str, Any]] = None,
    scheduler: Optional[CortexSchedulerService] = None,
    orchestrator: Optional["CortexV95Orchestrator"] = None,
) -> tuple[int, dict[str, Any]]:
    """Dispatch supported Command Center, live, history, and scheduler routes safely."""
    method = str(method).upper()
    payload = payload or {}
    route = path.split("?", 1)[0]

    if route == "/api/command-center/live":
        live_orchestrator = _shared_orchestrator(scheduler, orchestrator)
        return dispatch_dashboard_live(
            method,
            path,
            payload=payload,
            orchestrator=live_orchestrator,
        )

    if path.startswith("/api/scheduler"):
        return dispatch_scheduler_route(method, path, payload=payload, service=scheduler)

    if method == "GET" and route == "/api/cycles":
        if runtime_snapshot is None:
            runtime_snapshot = _shared_orchestrator(scheduler, orchestrator).runtime.snapshot()
        return dispatch_cycle_history_route(method, path, runtime_snapshot=runtime_snapshot)

    if method == "GET" and path == "/api/command-center":
        if runtime_snapshot is None and (orchestrator is not None or scheduler is not None):
            runtime_snapshot = _shared_orchestrator(scheduler, orchestrator).runtime.snapshot()
        return 200, build_command_center_snapshot(
            command=command,
            runtime_snapshot=runtime_snapshot,
            scheduler=scheduler,
        )

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
