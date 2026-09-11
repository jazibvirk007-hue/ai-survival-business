"""V9.5 integration coordinator for TJ Cortex.

Coordinates the stateful runtime, acquisition gate, Guard, communications and
learning surfaces without bypassing any existing execution boundary.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from cortex_autonomy_runtime import CortexAutonomyRuntime
from cortex_command_center import build_command_center_snapshot


class CortexV95Orchestrator:
    """Small integration boundary for repeated governed growth cycles."""

    def __init__(self, runtime: Optional[CortexAutonomyRuntime] = None) -> None:
        self.runtime = runtime if runtime is not None else CortexAutonomyRuntime()
        if not isinstance(self.runtime, CortexAutonomyRuntime):
            raise TypeError("runtime must be CortexAutonomyRuntime")

    def observe(self) -> Dict[str, Any]:
        """Return current runtime and command-center observations."""
        runtime_snapshot = self.runtime.snapshot()
        command_snapshot = build_command_center_snapshot(runtime_snapshot=runtime_snapshot)
        return {
            "runtime": runtime_snapshot,
            "command_center": command_snapshot,
        }

    def tick(self, *, execute: bool = False, approval_id: Optional[str] = None) -> Dict[str, Any]:
        """Advance exactly one bounded cycle; never loops unboundedly."""
        result = self.runtime.step(execute=execute, approval_id=approval_id)
        return {
            "cycle": result,
            "runtime": self.runtime.snapshot(),
        }

    def run_bounded(self, cycles: int = 1, *, execute: bool = False) -> Dict[str, Any]:
        """Run at most five bounded ticks and return every real observation."""
        if not isinstance(cycles, int) or isinstance(cycles, bool) or not 1 <= cycles <= 5:
            raise ValueError("cycles must be between 1 and 5")
        results = []
        for _ in range(cycles):
            results.append(self.tick(execute=execute))
        return {
            "engine": "Cortex V9.5 Autonomous Growth",
            "cycles_requested": cycles,
            "cycles_completed": len(results),
            "execute": bool(execute),
            "results": results,
            "runtime": self.runtime.snapshot(),
            "truth_policy": "verified revenue and payment truth remain authoritative",
        }


def build_v95_orchestrator(initial_state: Optional[Dict[str, Any]] = None) -> CortexV95Orchestrator:
    return CortexV95Orchestrator(CortexAutonomyRuntime(initial_state=initial_state))
