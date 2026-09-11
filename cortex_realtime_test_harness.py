"""Bounded local end-to-end smoke test for Cortex."""
from __future__ import annotations
import os, tempfile
from typing import Any, Dict
from cortex_autonomy_runtime import CortexAutonomyRuntime
from cortex_guard import CortexGuard
from cortex_learning import CortexLearning
from cortex_memory import CortexMemory
from cortex_communication import recent_messages
from cortex_v9_specialists import build_v9_loop

MAX_CYCLES = 5

def run_realtime_smoke_test(cycles: int = MAX_CYCLES) -> Dict[str, Any]:
    if not isinstance(cycles, int) or isinstance(cycles, bool) or not 1 <= cycles <= MAX_CYCLES:
        raise ValueError(f"cycles must be between 1 and {MAX_CYCLES}")
    with tempfile.TemporaryDirectory(prefix="cortex-realtime-") as workspace:
        previous = os.getcwd(); os.chdir(workspace)
        try:
            memory = CortexMemory(os.path.join(workspace, "memory.json"))
            learning = CortexLearning(memory)
            guard = CortexGuard(os.path.join(workspace, "approvals.json"))
            loop = build_v9_loop(learning=learning, guard=guard,
                communication_path=os.path.join(workspace, "communications.json"),
                ai_runtime=False, ai_selection=None, ai_enabled=False)
            runtime = CortexAutonomyRuntime(
                {"opportunity":"ai automation", "verified_revenue":0, "cash":0},
                loop=loop, max_history=50)
            before = {"verified_revenue": runtime.state.get("verified_revenue", 0), "cash": runtime.state.get("cash", 0)}
            results = []
            for _ in range(cycles):
                r = runtime.step(execute=True)
                results.append({"cycle_id":r.get("cycle_id"), "action":r.get("decision",{}).get("action"), "executed":bool(r.get("executed")), "state_changed":bool(r.get("state_changed"))})
            after = {"verified_revenue": runtime.state.get("verified_revenue", 0), "cash": runtime.state.get("cash", 0)}
            events = recent_messages(min(50, max(1, cycles * 4)), path=os.path.join(workspace, "communications.json"))
            memory_records = memory.recent(50)
            invariants = {
                "bounded_cycles": len(results) == cycles,
                "financial_truth_unchanged": after == before,
                "financial_patch_blocked": all(k not in h.get("applied_fields", []) for h in runtime.history for k in ("verified_revenue", "cash")),
                "communication_events_observed": bool(events),
                "learning_records_observed": len(memory_records) >= cycles,
                "no_outbound_send": all(not (isinstance(h.get("outcome"), dict) and h["outcome"].get("sent") is True) for h in runtime.history),
            }
            return {"engine":"Cortex Realtime Test Harness", "status":"PASS" if all(invariants.values()) else "FAIL", "mode":"controlled_local_execution", "cycles_requested":cycles, "cycles_completed":len(results), "results":results, "invariants":invariants, "financial_before":before, "financial_after":after, "communication_events":len(events), "learning_records":len(memory_records), "truth_policy":"no fabricated revenue; no outbound customer communication; no money movement"}
        finally:
            os.chdir(previous)
