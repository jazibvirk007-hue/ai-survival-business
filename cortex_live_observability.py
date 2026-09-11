"""Unified, read-only observability surface for the Cortex Command Center."""
from __future__ import annotations

from typing import Any, Mapping

from cortex_communication import communication_status, recent_messages
from cortex_cycle_history import build_cycle_history

MAX_EVENTS = 50


def build_live_observability(runtime_snapshot: Mapping[str, Any] | None, *, limit: int = 20) -> dict[str, Any]:
    """Combine bounded cycle and communication telemetry without execution authority."""
    cycles = build_cycle_history(runtime_snapshot, limit)
    try:
        events = recent_messages(min(MAX_EVENTS, max(1, int(limit))))
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
