"""Unified, browser-safe state surface for the Cortex Command Center."""

from __future__ import annotations

from typing import Any, Optional

from cortex_ai_command import CortexAICommand
from cortex_ai_health import build_ai_health
from cortex_communication import communication_status, recent_messages
from cortex_autonomy_health import evaluate_runtime_health
from cortex_cycle_history import build_cycle_history

MAX_EVENTS = 50
MAX_ERROR_TEXT = 500


def _safe_error(exc: Exception) -> str:
    text = str(exc).strip()
    return text[:MAX_ERROR_TEXT] if text else type(exc).__name__


def build_command_center_snapshot(
    *,
    command: Optional[CortexAICommand] = None,
    runtime_snapshot: Optional[dict[str, Any]] = None,
    scheduler: Optional[Any] = None,
    event_limit: int = MAX_EVENTS,
) -> dict[str, Any]:
    """Return a bounded snapshot suitable for direct browser consumption."""
    command = command or CortexAICommand()
    try:
        catalog = command.catalog()
    except Exception as exc:
        catalog = {"error": _safe_error(exc)}
    try:
        selected = command.selected()
    except Exception as exc:
        selected = {"selected": False, "error": _safe_error(exc)}
    try:
        ai_health = build_ai_health(command)
    except Exception as exc:
        ai_health = {"status": "DEGRADED", "error": _safe_error(exc)}

    try:
        communication = {
            "status": communication_status(),
            "events": recent_messages(limit=max(1, min(int(event_limit), MAX_EVENTS))),
        }
    except Exception as exc:
        communication = {"status": "DEGRADED", "events": [], "error": _safe_error(exc)}

    runtime_health = None
    cycle_history = {"status": "UNAVAILABLE", "count": 0, "cycles": []}
    if runtime_snapshot is not None:
        try:
            runtime_health = evaluate_runtime_health(runtime_snapshot)
        except Exception as exc:
            runtime_health = {"status": "INVALID_SNAPSHOT", "error": _safe_error(exc)}
        try:
            cycle_history = build_cycle_history(runtime_snapshot, limit=min(event_limit, 50))
        except Exception as exc:
            cycle_history = {"status": "DEGRADED", "count": 0, "cycles": [], "error": _safe_error(exc)}

    scheduler_snapshot = None
    try:
        if scheduler is None:
            from cortex_scheduler_service import CortexSchedulerService
            scheduler = CortexSchedulerService()
        scheduler_snapshot = scheduler.snapshot()
    except Exception as exc:
        scheduler_snapshot = {"status": "DEGRADED", "error": _safe_error(exc)}

    return {
        "engine": "Cortex Command Center",
        "version": "9.5.2",
        "ai": {"catalog": catalog, "selected": selected, "health": ai_health},
        "communications": communication,
        "runtime_health": runtime_health,
        "cycle_history": cycle_history,
        "scheduler": scheduler_snapshot,
        "truth_policy": {
            "revenue": "verified observations only",
            "credentials": "server-side only",
            "execution": "governed",
            "scheduler": "bounded and safety-pausable",
            "history": "observational audit only",
        },
    }
