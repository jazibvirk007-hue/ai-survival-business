from __future__ import annotations

from typing import Any, Mapping

MAX_CYCLES = 50
MAX_TEXT = 500


def _safe_outcome(value: Any) -> dict[str, Any]:
    """Expose only bounded, non-payload outcome fields to the browser."""
    if not isinstance(value, dict):
        return {}
    return {
        "success": bool(value.get("success", False)),
        "status": str(value.get("status", ""))[:100],
        "summary": str(value.get("summary", ""))[:MAX_TEXT],
    }


def _safe_trace(value: Any) -> dict[str, Any]:
    """Keep the already-audited cycle trace bounded and dictionary-only."""
    if not isinstance(value, dict):
        return {}
    allowed = {
        "cycle_id",
        "decision",
        "execution",
        "outcome",
        "communication",
        "learning",
        "state",
        "truth_policy",
    }
    trace = {key: value[key] for key in allowed if key in value}
    return trace


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
        applied = item.get("applied_fields", [])
        cycles.append(
            {
                "cycle_id": str(item.get("cycle_id", "unknown"))[:MAX_TEXT],
                "action": str(item.get("action", "unknown"))[:MAX_TEXT],
                "executed": bool(item.get("executed", False)),
                "outcome": _safe_outcome(item.get("outcome")),
                "applied_fields": [str(x)[:100] for x in applied][:20] if isinstance(applied, list) else [],
                "cycle_trace": _safe_trace(item.get("cycle_trace")),
            }
        )

    cycles.reverse()
    return {"status": "READY", "count": len(cycles), "cycles": cycles, "max_cycles": MAX_CYCLES}
