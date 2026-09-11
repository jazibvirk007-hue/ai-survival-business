"""Health/readiness checks for the Cortex autonomous runtime."""

from __future__ import annotations

from typing import Any, Mapping


REQUIRED_KEYS = ("engine", "version", "registered_actions", "truth_policy")


def evaluate_runtime_health(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Return conservative readiness information without fabricating business metrics."""
    if not isinstance(snapshot, Mapping):
        return {"ready": False, "status": "INVALID_SNAPSHOT", "checks": {"snapshot": False}}
    checks = {
        "snapshot": all(key in snapshot for key in REQUIRED_KEYS),
        "actions_registered": bool(snapshot.get("registered_actions")),
        "truth_policy_present": "verified" in str(snapshot.get("truth_policy", "")).lower(),
        "state_object": isinstance(snapshot.get("state"), Mapping),
    }
    ready = all(checks.values())
    return {
        "ready": ready,
        "status": "READY" if ready else "DEGRADED",
        "checks": checks,
        "history_count": max(0, int(snapshot.get("history_count", 0) or 0)) if str(snapshot.get("history_count", "0")).lstrip("-").isdigit() else 0,
    }
