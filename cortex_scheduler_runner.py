"""Bounded scheduler runner for live Cortex observation cycles.

This runner deliberately uses decision-only scheduler ticks. Any external,
customer-facing, financial, or irreversible execution remains behind the
existing approval and verification boundaries.
"""
from __future__ import annotations

import threading
from typing import Any, Optional

from cortex_scheduler_service import CortexSchedulerService

DEFAULT_INTERVAL_SECONDS = 30.0
MAX_INTERVAL_SECONDS = 3600.0
MAX_CYCLES_PER_RUN = 1000


class CortexSchedulerRunner:
    """Run bounded decision-only cycles until stopped or safety pause."""

    def __init__(self, scheduler: Optional[CortexSchedulerService] = None, *, interval_seconds: float = DEFAULT_INTERVAL_SECONDS) -> None:
        if not isinstance(interval_seconds, (int, float)) or isinstance(interval_seconds, bool):
            raise ValueError("interval_seconds must be numeric")
        if not 0.1 <= float(interval_seconds) <= MAX_INTERVAL_SECONDS:
            raise ValueError("interval_seconds out of bounds")
        self.scheduler = scheduler or CortexSchedulerService()
        self.interval_seconds = float(interval_seconds)
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    @property
    def stopped(self) -> bool:
        return self._stop.is_set()

    def run(self, *, max_cycles: Optional[int] = None) -> dict[str, Any]:
        if max_cycles is not None:
            if not isinstance(max_cycles, int) or isinstance(max_cycles, bool):
                raise ValueError("max_cycles must be an integer")
            if not 1 <= max_cycles <= MAX_CYCLES_PER_RUN:
                raise ValueError("max_cycles out of bounds")
        results: list[dict[str, Any]] = []
        while not self.stopped and (max_cycles is None or len(results) < max_cycles):
            result = self.scheduler.tick(execute=False)
            results.append(result)
            state = result.get("scheduler", {}) if isinstance(result, dict) else {}
            if state.get("recovery") == "automatic_safety_pause":
                break
            if self.stopped or (max_cycles is not None and len(results) >= max_cycles):
                break
            self._stop.wait(self.interval_seconds)
        return {
            "engine": "Cortex Scheduler Runner",
            "cycles_completed": len(results),
            "stopped": self.stopped,
            "scheduler": self.scheduler.snapshot(),
            "results": results,
            "truth_policy": "decision-only runner; no external execution or financial truth mutation",
        }

    def run_once(self) -> dict[str, Any]:
        return self.scheduler.tick(execute=False)
