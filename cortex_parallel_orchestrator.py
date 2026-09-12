"""Bounded parallel workstream coordinator for Cortex.

Coordinates independent observation/validation work without allowing more than
one irreversible business transition per cycle. Workers are intentionally
injected so this module does not invent external facts or perform payments.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Optional


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
        """Run read/planning workers in parallel conceptually, with no side effects."""
        observations: Dict[str, Any] = {}
        for name, worker in self.workstreams.items():
            result = worker(dict(state))
            observations[name] = result if isinstance(result, dict) else {"result": result}
        return {"observations": observations, "truth_policy": "verified_observations_only"}

    def decide(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Select at most one transition from worker proposals."""
        candidates = []
        for name, result in observations.get("observations", {}).items():
            if not isinstance(result, dict):
                continue
            action = result.get("action")
            if action:
                candidates.append((name, action, result.get("reason", "")))
        if not candidates:
            return {"action": None, "workstream": None, "transition_budget": 0}
        name, action, reason = candidates[0]
        return {
            "action": action,
            "workstream": name,
            "reason": reason,
            "transition_budget": self.MAX_TRANSITIONS_PER_CYCLE,
        }

    def cycle(self, state: Dict[str, Any]) -> Dict[str, Any]:
        observations = self.observe(state)
        decision = self.decide(observations)
        return {"observations": observations, "decision": decision, "execution": "decision_only"}

    def status(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "workstreams": sorted(self.workstreams),
            "max_transitions_per_cycle": self.MAX_TRANSITIONS_PER_CYCLE,
            "execution": "decision_only",
            "revenue": "verified_observations_only",
        }
