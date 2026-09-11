"""Bounded, browser-safe trace for one Cortex autonomous cycle."""

from __future__ import annotations

from typing import Any, Dict

MAX_TEXT = 600
MAX_ITEMS = 20


def _text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    return str(value)[:MAX_TEXT]


def build_cycle_trace(result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract an auditable lifecycle trace without changing engine authority."""
    if not isinstance(result, dict):
        raise TypeError("result must be a dictionary")

    decision = result.get("decision") if isinstance(result.get("decision"), dict) else {}
    outcome = result.get("outcome")
    if isinstance(outcome, dict):
        outcome_view = {
            "success": outcome.get("success"),
            "summary": _text(outcome.get("summary", outcome.get("message", ""))),
        }
    else:
        outcome_view = {"success": None, "summary": _text(outcome)}

    return {
        "cycle_id": _text(result.get("cycle_id"), "unknown"),
        "decision": {
            "action": _text(decision.get("action"), "unknown"),
            "priority": decision.get("priority", 0),
            "approval_required": bool(decision.get("approval_required", False)),
        },
        "execution": {
            "executed": bool(result.get("executed")),
            "status": _text(result.get("status", "")),
        },
        "outcome": outcome_view,
        "communication": {
            "events_observed": len(result.get("communication_events", [])) if isinstance(result.get("communication_events"), list) else 0,
        },
        "learning": {
            "recorded": bool(result.get("learning_recorded", result.get("learned", False))),
        },
        "state": {
            "changed": bool(result.get("state_changed", False)),
            "applied_fields": list(result.get("applied_state_patch", {}).keys())[:MAX_ITEMS] if isinstance(result.get("applied_state_patch"), dict) else [],
        },
        "truth_policy": "financial truth is verified-only; trace is observational",
    }
