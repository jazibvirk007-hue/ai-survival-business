"""Bounded scheduler for repeated Cortex autonomy cycles.

The scheduler is intentionally framework-neutral. It does not spawn unbounded
threads or invent work. A host process can call ``tick`` on its own schedule.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from cortex_v95_orchestrator import CortexV95Orchestrator

MAX_CONSECUTIVE_FAILURES = 3
MAX_CYCLES_PER_INVOCATION = 5


@dataclass(frozen=True)
class SchedulerDecision:
    action: str
    reason: str
    execute: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "reason": self.reason,
            "execute": self.execute,
        }


class CortexAutonomousScheduler:
    """Plan bounded runtime invocations and recover conservatively."""

    def __init__(
        self,
        orchestrator: Optional[CortexV95Orchestrator] = None,
        *,
        max_consecutive_failures: int = MAX_CONSECUTIVE_FAILURES,
    ) -> None:
        if max_consecutive_failures < 1 or max_consecutive_failures > 10:
            raise ValueError("max_consecutive_failures must be between 1 and 10")
        self.orchestrator = orchestrator or CortexV95Orchestrator()
        self.max_consecutive_failures = max_consecutive_failures
        self.consecutive_failures = 0
        self.total_ticks = 0
        self.last_result: Optional[dict[str, Any]] = None
        self.last_tick_at: Optional[str] = None
        self.paused = False

    def plan(self, *, execute: bool = False) -> SchedulerDecision:
        if not isinstance(execute, bool):
            raise ValueError("execute must be boolean")
        if self.paused:
            return SchedulerDecision("pause", "failure_recovery_pause", False)
        return SchedulerDecision("tick", "bounded_runtime_cycle", execute)

    def tick(self, *, execute: bool = False, approval_id: Optional[str] = None) -> dict[str, Any]:
        decision = self.plan(execute=execute)
        if decision.action == "pause":
            return {
                "ok": True,
                "status": "PAUSED",
                "decision": decision.to_dict(),
                "consecutive_failures": self.consecutive_failures,
            }

        result = self.orchestrator.tick(execute=decision.execute, approval_id=approval_id)
        self.total_ticks += 1
        self.last_tick_at = datetime.now(timezone.utc).isoformat()
        self.last_result = result

        outcome = result.get("outcome") or {}
        failed = bool(outcome.get("failed"))
        if failed:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0

        if self.consecutive_failures >= self.max_consecutive_failures:
            self.paused = True

        return {
            "ok": True,
            "status": "PAUSED" if self.paused else "RUNNING",
            "decision": decision.to_dict(),
            "result": result,
            "total_ticks": self.total_ticks,
            "consecutive_failures": self.consecutive_failures,
            "recovery": "manual_resume_required" if self.paused else "normal",
        }

    def resume(self) -> dict[str, Any]:
        self.paused = False
        self.consecutive_failures = 0
        return {"ok": True, "status": "RUNNING", "recovery": "reset_after_pause"}

    def status(self) -> dict[str, Any]:
        return {
            "engine": "Cortex Autonomous Scheduler",
            "version": "9.5",
            "status": "PAUSED" if self.paused else "RUNNING",
            "total_ticks": self.total_ticks,
            "consecutive_failures": self.consecutive_failures,
            "max_consecutive_failures": self.max_consecutive_failures,
            "max_cycles_per_invocation": MAX_CYCLES_PER_INVOCATION,
            "last_tick_at": self.last_tick_at,
            "recovery": "manual_resume_required" if self.paused else "normal",
            "truth_policy": "scheduler never creates revenue or financial truth",
        }
