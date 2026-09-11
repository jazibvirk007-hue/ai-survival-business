"""Bounded local end-to-end smoke test for Cortex."""
from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Dict

from cortex_autonomy_runtime import CortexAutonomyRuntime
from cortex_guard import CortexGuard
from cortex_learning import CortexLearning
from cortex_memory import CortexMemory
from cortex_communication import recent_messages
from cortex_v9_specialists import build_v9_loop

MAX_CYCLES = 5


def _build_runtime(workspace: str) -> CortexAutonomyRuntime:
    memory = CortexMemory(os.path.join(workspace, "memory.json"))
    learning = CortexLearning(memory)
    guard = CortexGuard(os.path.join(workspace, "approvals.json"))
    loop = build_v9_loop(
        learning=learning,
        guard=guard,
        communication_path=os.path.join(workspace, "communications.json"),
        ai_runtime=False,
        ai_selection=None,
        ai_enabled=False,
    )
    return CortexAutonomyRuntime(
        {"opportunity": "ai automation", "verified_revenue": 0, "cash": 0},
        loop=loop,
        max_history=50,
        state_path=os.path.join(workspace, "runtime_state.json"),
    )


def run_realtime_smoke_test(cycles: int = MAX_CYCLES) -> Dict[str, Any]:
    if not isinstance(cycles, int) or isinstance(cycles, bool) or not 1 <= cycles <= MAX_CYCLES:
        raise ValueError(f"cycles must be between 1 and {MAX_CYCLES}")

    with tempfile.TemporaryDirectory(prefix="cortex-realtime-") as workspace:
        previous = os.getcwd()
        os.chdir(workspace)
        try:
            runtime = _build_runtime(workspace)
            before = {
                "verified_revenue": runtime.state.get("verified_revenue", 0),
                "cash": runtime.state.get("cash", 0),
            }
            results = []
            for _ in range(cycles):
                result = runtime.step(execute=True)
                results.append({
                    "cycle_id": result.get("cycle_id"),
                    "action": result.get("decision", {}).get("action"),
                    "executed": bool(result.get("executed")),
                    "state_changed": bool(result.get("state_changed")),
                })

            after = {
                "verified_revenue": runtime.state.get("verified_revenue", 0),
                "cash": runtime.state.get("cash", 0),
            }
            persisted_state = dict(runtime.state)
            persisted_history = list(runtime.history)

            # Restart from the same persisted workspace. The persisted state must
            # win over any caller-supplied bootstrap values.
            restarted = _build_runtime(workspace)
            restart_ok = (
                restarted.persistence_status == "restored"
                and restarted.state == persisted_state
                and restarted.history == persisted_history
            )

            events = recent_messages(
                min(50, max(1, cycles * 4)),
                path=os.path.join(workspace, "communications.json"),
            )
            memory_records = runtime.loop.learning.memory.recent(50)

            # Corrupt persisted state must fail closed instead of silently
            # executing from a replacement bootstrap state.
            corrupt_path = os.path.join(workspace, "corrupt_state.json")
            with open(corrupt_path, "w", encoding="utf-8") as handle:
                handle.write("{not-valid-json")
            corrupt_closed = False
            try:
                _build_corrupt_runtime(workspace, corrupt_path)
            except ValueError:
                corrupt_closed = True

            invariants = {
                "bounded_cycles": len(results) == cycles,
                "financial_truth_unchanged": after == before,
                "financial_patch_blocked": all(
                    key not in history_item.get("applied_fields", [])
                    for history_item in runtime.history
                    for key in ("verified_revenue", "cash")
                ),
                "communication_events_observed": bool(events),
                "learning_records_observed": len(memory_records) >= cycles,
                "no_outbound_send": all(
                    not (
                        isinstance(history_item.get("outcome"), dict)
                        and history_item["outcome"].get("sent") is True
                    )
                    for history_item in runtime.history
                ),
                "restart_restored_state": restart_ok,
                "corrupt_state_fails_closed": corrupt_closed,
            }
            return {
                "engine": "Cortex Realtime Test Harness",
                "status": "PASS" if all(invariants.values()) else "FAIL",
                "mode": "controlled_local_execution",
                "cycles_requested": cycles,
                "cycles_completed": len(results),
                "results": results,
                "invariants": invariants,
                "financial_before": before,
                "financial_after": after,
                "communication_events": len(events),
                "learning_records": len(memory_records),
                "restart_persistence": {
                    "restored": restart_ok,
                    "history_count": len(restarted.history),
                },
                "truth_policy": "no fabricated revenue; no outbound customer communication; no money movement",
            }
        finally:
            os.chdir(previous)


def _build_corrupt_runtime(workspace: str, corrupt_path: str) -> CortexAutonomyRuntime:
    memory = CortexMemory(os.path.join(workspace, "corrupt-memory.json"))
    learning = CortexLearning(memory)
    guard = CortexGuard(os.path.join(workspace, "corrupt-approvals.json"))
    loop = build_v9_loop(
        learning=learning,
        guard=guard,
        communication_path=os.path.join(workspace, "corrupt-communications.json"),
        ai_runtime=False,
        ai_selection=None,
        ai_enabled=False,
    )
    return CortexAutonomyRuntime(
        {"opportunity": "bootstrap-must-not-run", "verified_revenue": 999, "cash": 999},
        loop=loop,
        max_history=20,
        state_path=corrupt_path,
    )
