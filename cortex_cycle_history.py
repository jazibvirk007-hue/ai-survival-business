from __future__ import annotations
from typing import Any, Mapping

MAX_CYCLES = 50


def build_cycle_history(runtime_snapshot: Mapping[str, Any] | None, limit: int = 20) -> dict[str, Any]:
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_CYCLES:
        raise ValueError("invalid limit")
    if runtime_snapshot is None:
        return {"status": "UNAVAILABLE", "count": 0, "cycles": []}
    history = runtime_snapshot.get("history", [])
    if not isinstance(history, list):
        return {"status": "DEGRADED", "count": 0, "cycles": []}
    cycles = []
    for item in history[-limit:]:
        if not isinstance(item, dict):
            continue
        cycles.append({"cycle_id": str(item.get("cycle_id", "unknown"))[:300], "action": str(item.get("action", "unknown"))[:300], "executed": bool(item.get("executed", False)), "outcome": item.get("outcome") if isinstance(item.get("outcome"), dict) else {}, "applied_fields": [str(x)[:100] for x in item.get("applied_fields", [])][:20] if isinstance(item.get("applied_fields"), list) else [], "cycle_trace": item.get("cycle_trace") if isinstance(item.get("cycle_trace"), dict) else {}})
    cycles.reverse()
    return {"status": "READY", "count": len(cycles), "cycles": cycles, "max_cycles": MAX_CYCLES}
