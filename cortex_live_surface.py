"""Single-source live observation surface for the Cortex Command Center.

This adapter keeps browser telemetry tied to one orchestrator/runtime instance.
It is read-only and has no financial, credential, or outbound-channel authority.
"""
from __future__ import annotations

from typing import Any, Optional

from cortex_command_center import build_command_center_snapshot
from cortex_live_observability import build_live_observability
from cortex_v95_orchestrator import CortexV95Orchestrator

MAX_EVENTS = 50


def build_live_surface(
    orchestrator: CortexV95Orchestrator,
    *,
    limit: int = 20,
) -> dict[str, Any]:
    if not isinstance(orchestrator, CortexV95Orchestrator):
        raise TypeError("orchestrator must be CortexV95Orchestrator")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_EVENTS:
        raise ValueError("invalid limit")

    runtime_snapshot = orchestrator.runtime.snapshot()
    command_center = build_command_center_snapshot(
        runtime_snapshot=runtime_snapshot,
        event_limit=limit,
    )
    observability = build_live_observability(runtime_snapshot, limit=limit)

    return {
        "engine": "Cortex Live Surface",
        "version": "1.0",
        "command_center": command_center,
        "observability": observability,
        "runtime": {
            "persistence": runtime_snapshot.get("persistence", {}),
            "history_count": runtime_snapshot.get("history_count", 0),
        },
        "truth_policy": "read-only observation; execution remains behind governed scheduler and Guard",
    }


def live_surface_status(orchestrator: Optional[CortexV95Orchestrator] = None) -> dict[str, Any]:
    """Return a minimal browser-safe readiness state."""
    if orchestrator is None:
        return {
            "status": "READY",
            "engine": "Cortex Live Surface",
            "shared_runtime": True,
            "truth_policy": "read-only observation",
        }
    if not isinstance(orchestrator, CortexV95Orchestrator):
        raise TypeError("orchestrator must be CortexV95Orchestrator")
    return {
        "status": "READY",
        "engine": "Cortex Live Surface",
        "shared_runtime": True,
        "persistence": orchestrator.runtime.snapshot().get("persistence", {}),
        "truth_policy": "read-only observation",
    }
