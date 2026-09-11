"""Unified, read-only observability surface for the Cortex Command Center."""
from __future__ import annotations

from typing import Any, Mapping

from cortex_communication import communication_status, recent_messages
from cortex_cycle_history import build_cycle_history

MAX_EVENTS = 50
MAX_SUMMARY = 500


def _safe_outcome(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {"success": bool(value.get("success", False)), "summary": str(value.get("summary", ""))[:MAX_SUMMARY]}


def build_live_observability(runtime_snapshot: Mapping[str, Any] | None, *, limit: int = 20) -> dict[str, Any]:
    """Combine bounded cycle and communication telemetry without execution authority."""
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_EVENTS:
        raise ValueError("invalid limit")
    cycles = build_cycle_history(runtime_snapshot, limit)
    if cycles.get("status") == "READY":
        cycles = {
            **cycles,
            "cycles": [
                {
                    "cycle_id": str(c.get("cycle_id", "unknown"))[:300],
                    "action": str(c.get("action", "unknown"))[:300],
                    "executed": bool(c.get("executed", False)),
                    "outcome": _safe_outcome(c.get("outcome")),
                    "applied_fields": [str(x)[:100] for x in c.get("applied_fields", [])][:20] if isinstance(c.get("applied_fields"), list) else [],
                    "cycle_trace": c.get("cycle_trace") if isinstance(c.get("cycle_trace"), dict) else {},
                }
                for c in cycles.get("cycles", []) if isinstance(c, dict)
            ],
        }
    try:
        events = recent_messages(min(MAX_EVENTS, limit))
    except Exception:
        events = []
    try:
        stream = communication_status()
    except Exception:
        stream = {"enabled": False, "events": 0, "live_stream_ready": False}
    return {
        "status": "READY" if cycles.get("status") == "READY" else cycles.get("status", "DEGRADED"),
        "cycles": cycles,
        "communications": {"events": events, "stream": stream},
        "truth_policy": "observational only; no execution, financial, customer, or credential authority",
    }
