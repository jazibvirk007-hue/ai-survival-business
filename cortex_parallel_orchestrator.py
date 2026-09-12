"""Bounded parallel workstream coordinator for Cortex.

Independent workers may observe and plan in the same cycle. Execution remains
bounded to one irreversible transition and is deliberately delegated to the
existing Guard/CEOLoop layers.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional


class CortexParallelOrchestrator:
    VERSION = "15.0"
    MAX_TRANSITIONS_PER_CYCLE = 1

    def __init__(self, workstreams: Optional[Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]]] = None):
        self.workstreams = dict(workstreams or {})

    def register(self, name: str, worker: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        if not name or not callable(worker):
            raise ValueError("workstream name and callable worker are required")
        self.workstreams[name] = worker

    def observe(self, state: Dict[str, Any]) -> Dict[str, Any]:
        observations: Dict[str, Any] = {}
        for name, worker in self.workstreams.items():
            result = worker(dict(state))
            observations[name] = result if isinstance(result, dict) else {"result": result}
        return {"observations": observations, "truth_policy": "verified_observations_only"}

    def decide(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        for name, result in observations.get("observations", {}).items():
            if isinstance(result, dict) and result.get("action"):
                return {
                    "action": result["action"],
                    "workstream": name,
                    "reason": result.get("reason", ""),
                    "transition_budget": self.MAX_TRANSITIONS_PER_CYCLE,
                }
        return {"action": None, "workstream": None, "transition_budget": 0}

    def cycle(self, state: Dict[str, Any]) -> Dict[str, Any]:
        observations = self.observe(state)
        return {
            "observations": observations,
            "decision": self.decide(observations),
            "execution": "decision_only",
        }

    def status(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "workstreams": sorted(self.workstreams),
            "max_transitions_per_cycle": self.MAX_TRANSITIONS_PER_CYCLE,
            "execution": "decision_only",
            "revenue": "verified_observations_only",
        }
