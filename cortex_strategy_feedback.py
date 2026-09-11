"""Connect observed Deep Memory signals to the CEO as bounded advisory context."""

from __future__ import annotations

from typing import Any, Dict

from cortex_deep_memory import CortexDeepMemory

MAX_CONTEXT = 10


class CortexStrategyFeedback:
    """Build non-authoritative strategy context from observed outcomes."""

    def __init__(self, deep_memory: CortexDeepMemory):
        if not isinstance(deep_memory, CortexDeepMemory):
            raise TypeError("deep_memory must be CortexDeepMemory")
        self.deep_memory = deep_memory

    def build(self, limit: int = MAX_CONTEXT) -> Dict[str, Any]:
        if not isinstance(limit, int) or not 1 <= limit <= MAX_CONTEXT:
            raise ValueError("limit out of bounds")
        context = self.deep_memory.context(limit)
        recommendations = []
        for row in context:
            if not isinstance(row, dict):
                continue
            rate = row.get("success_rate")
            observed = row.get("observed_outcomes", 0)
            action = row.get("action")
            if not isinstance(action, str) or not isinstance(observed, int) or observed < 2:
                continue
            if isinstance(rate, (int, float)) and rate < 0.35:
                recommendations.append({"action": action, "signal": "deprioritize", "reason": "Observed outcome rate is weak."})
            elif isinstance(rate, (int, float)) and rate >= 0.80:
                recommendations.append({"action": action, "signal": "favor", "reason": "Observed outcome rate is strong."})
        return {
            "engine": "Cortex Strategy Feedback",
            "status": "READY" if context else "WAITING_FOR_OBSERVATIONS",
            "context": context,
            "recommendations": recommendations[:MAX_CONTEXT],
            "authority": "advisory_only",
            "truth_policy": "observed outcomes only; never authorizes execution",
        }


def enrich_ceo_state(state: Dict[str, Any], feedback: CortexStrategyFeedback) -> Dict[str, Any]:
    """Return a copy of state enriched with bounded learning context."""
    if not isinstance(state, dict):
        raise TypeError("state must be a dictionary")
    if not isinstance(feedback, CortexStrategyFeedback):
        raise TypeError("feedback must be CortexStrategyFeedback")
    enriched = dict(state)
    snapshot = feedback.build()
    enriched["memory_strategy"] = snapshot["context"]
    return enriched
