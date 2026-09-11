"""Unified browser-safe control surface for Cortex V9.5."""

from __future__ import annotations

from typing import Any, Optional

from cortex_command_center import build_command_center_snapshot
from cortex_v95_orchestrator import CortexV95Orchestrator

MAX_CYCLES = 5


def build_v95_command_snapshot(
    orchestrator: Optional[CortexV95Orchestrator] = None,
    *,
    event_limit: int = 50,
) -> dict[str, Any]:
    """Compose Command Center telemetry with the live V9.5 runtime."""
    orchestrator = orchestrator or CortexV95Orchestrator()
    observation = orchestrator.observe()
    return {
        "command_center": build_command_center_snapshot(
            runtime_snapshot=observation["runtime"],
            event_limit=event_limit,
        ),
        "v95": {
            "engine": "Cortex V9.5 Autonomous Growth",
            "control": "bounded",
            "max_cycles": MAX_CYCLES,
            "runtime": observation["runtime"],
        },
    }


def run_v95_command(
    command: dict[str, Any],
    *,
    orchestrator: Optional[CortexV95Orchestrator] = None,
) -> dict[str, Any]:
    """Execute only an explicitly requested bounded runtime command."""
    if not isinstance(command, dict) or len(command) > 10:
        return {"ok": False, "error": "invalid_command"}
    action = command.get("action", "observe")
    if action == "observe":
        return {"ok": True, **build_v95_command_snapshot(orchestrator)}
    if action not in {"tick", "run"}:
        return {"ok": False, "error": "unsupported_action"}
    execute = command.get("execute", False)
    if not isinstance(execute, bool):
        return {"ok": False, "error": "execute_must_be_boolean"}
    orchestrator = orchestrator or CortexV95Orchestrator()
    if action == "tick":
        approval_id = command.get("approval_id")
        if approval_id is not None and (not isinstance(approval_id, str) or not approval_id.strip() or len(approval_id) > 200):
            return {"ok": False, "error": "invalid_approval_id"}
        return {"ok": True, **orchestrator.tick(execute=execute, approval_id=approval_id)}
    cycles = command.get("cycles", 1)
    if not isinstance(cycles, int) or isinstance(cycles, bool) or not 1 <= cycles <= MAX_CYCLES:
        return {"ok": False, "error": "cycles_must_be_between_1_and_5"}
    return {"ok": True, **orchestrator.run_bounded(cycles, execute=execute)}
