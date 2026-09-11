"""Persistent, bounded scheduler service for Cortex."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from cortex_autonomous_scheduler import CortexAutonomousScheduler
from cortex_scheduler_persistence import load_scheduler_state, save_scheduler_state
from cortex_v95_orchestrator import CortexV95Orchestrator

MAX_CONSECUTIVE_FAILURES = 3


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CortexSchedulerService:
    """Restore scheduler state, run bounded work, and persist recovery state."""

    def __init__(self, orchestrator: Optional[CortexV95Orchestrator] = None, state_path: str = "cortex_scheduler_state.json"):
        self.orchestrator = orchestrator or CortexV95Orchestrator()
        self.state_path = state_path
        try:
            self.state = load_scheduler_state(state_path)
        except ValueError:
            self.state = {"paused": True, "consecutive_failures": MAX_CONSECUTIVE_FAILURES, "recovery": "corrupt_state"}
        self.state.setdefault("paused", False)
        self.state.setdefault("consecutive_failures", 0)
        self.state.setdefault("cycles_completed", 0)
        self.state.setdefault("last_run", None)

    def snapshot(self) -> dict[str, Any]:
        return {
            "engine": "Cortex Persistent Scheduler",
            "status": "PAUSED" if self.state["paused"] else "READY",
            "paused": bool(self.state["paused"]),
            "consecutive_failures": int(self.state["consecutive_failures"]),
            "cycles_completed": int(self.state["cycles_completed"]),
            "last_run": self.state["last_run"],
            "recovery": self.state.get("recovery", "normal"),
            "truth_policy": "scheduler never writes financial truth",
        }

    def resume(self) -> dict[str, Any]:
        self.state["paused"] = False
        self.state["consecutive_failures"] = 0
        self.state["recovery"] = "manual_resume"
        save_scheduler_state(self.state, self.state_path)
        return self.snapshot()

    def tick(self, *, execute: bool = False, approval_id: Optional[str] = None) -> dict[str, Any]:
        if not isinstance(execute, bool):
            raise ValueError("execute must be boolean")
        if self.state["paused"]:
            return {"ok": False, "error": "scheduler_paused", "scheduler": self.snapshot()}
        try:
            result = self.orchestrator.tick(execute=execute, approval_id=approval_id)
            self.state["cycles_completed"] += 1
            self.state["consecutive_failures"] = 0
            self.state["last_run"] = _now()
            self.state["recovery"] = "normal"
            save_scheduler_state(self.state, self.state_path)
            return {"ok": True, "result": result, "scheduler": self.snapshot()}
        except Exception:
            self.state["consecutive_failures"] += 1
            self.state["last_run"] = _now()
            if self.state["consecutive_failures"] >= MAX_CONSECUTIVE_FAILURES:
                self.state["paused"] = True
                self.state["recovery"] = "automatic_safety_pause"
            save_scheduler_state(self.state, self.state_path)
            return {"ok": False, "error": "cycle_failed", "scheduler": self.snapshot()}
