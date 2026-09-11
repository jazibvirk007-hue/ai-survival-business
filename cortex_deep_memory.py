"""Deep business memory derived only from observed Cortex learning records."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from cortex_memory import CortexMemory

MAX_RECORDS = 200
MAX_ACTIONS = 50


class CortexDeepMemory:
    """Turn bounded observations into explainable strategy signals.

    Advisory only: it cannot execute actions, alter financial truth, or
    manufacture outcomes. It summarizes observed decisions/outcomes.
    """

    def __init__(self, memory: CortexMemory | None = None):
        self.memory = memory or CortexMemory()
        if not isinstance(self.memory, CortexMemory):
            raise TypeError("memory must be a CortexMemory")

    def _records(self, limit: int = MAX_RECORDS) -> list[dict[str, Any]]:
        if not isinstance(limit, int) or not 1 <= limit <= MAX_RECORDS:
            raise ValueError("limit out of bounds")
        rows = self.memory.recent(limit)
        return [row for row in rows if isinstance(row, dict)]

    def analyze(self, limit: int = MAX_RECORDS) -> dict[str, Any]:
        rows = self._records(limit)
        actions: dict[str, dict[str, int]] = defaultdict(lambda: {"decisions": 0, "successes": 0, "failures": 0})
        for row in rows:
            kind = row.get("kind")
            content = row.get("content")
            if not isinstance(content, str) or ":" not in content:
                continue
            action = content.split(":", 1)[0].strip()
            if not action or len(action) > 200:
                continue
            if kind == "decision":
                actions[action]["decisions"] += 1
            elif kind == "outcome":
                success = (row.get("metadata") or {}).get("success")
                if success is True:
                    actions[action]["successes"] += 1
                elif success is False:
                    actions[action]["failures"] += 1

        ranked = []
        for action, stats in actions.items():
            observed = stats["successes"] + stats["failures"]
            rate = (stats["successes"] / observed) if observed else None
            ranked.append({"action": action, **stats, "observed_outcomes": observed, "success_rate": rate})
        ranked.sort(key=lambda item: (item["observed_outcomes"], item["success_rate"] if item["success_rate"] is not None else -1), reverse=True)
        ranked = ranked[:MAX_ACTIONS]

        observed_outcomes = sum(item["observed_outcomes"] for item in ranked)
        successes = sum(item["successes"] for item in ranked)
        failures = sum(item["failures"] for item in ranked)
        return {
            "engine": "Cortex Deep Memory",
            "status": "READY" if rows else "WAITING_FOR_OBSERVATIONS",
            "records_considered": len(rows),
            "actions": ranked,
            "observed_outcomes": observed_outcomes,
            "successes": successes,
            "failures": failures,
            "overall_success_rate": (successes / observed_outcomes) if observed_outcomes else None,
            "truth_policy": "observed learning records only",
            "execution_authority": "none",
        }

    def context(self, limit: int = 10) -> list[dict[str, Any]]:
        snapshot = self.analyze()
        return snapshot["actions"][:max(1, min(int(limit), MAX_ACTIONS))]
