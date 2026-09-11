"""Measurable business goals for TJ Cortex.

Goals are planning data only: this module never invents performance and never
executes spending, customer outreach, or other external actions.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class Goal:
    name: str
    metric: str
    target: float
    deadline_days: Optional[float] = None
    priority: float = 50.0

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("goal name must be non-empty")
        if not isinstance(self.metric, str) or not self.metric.strip():
            raise ValueError("goal metric must be non-empty")
        if not isinstance(self.target, (int, float)) or self.target != self.target:
            raise ValueError("goal target must be numeric")
        if self.deadline_days is not None and (not isinstance(self.deadline_days, (int, float)) or self.deadline_days < 0):
            raise ValueError("deadline_days must be non-negative")
        if not isinstance(self.priority, (int, float)) or not 0 <= self.priority <= 100:
            raise ValueError("priority must be between 0 and 100")


class CortexGoalEngine:
    """Evaluate explicit goals against observed business telemetry."""

    def __init__(self, goals: Optional[Iterable[Goal]] = None) -> None:
        self.goals: List[Goal] = list(goals or [])
        if any(not isinstance(goal, Goal) for goal in self.goals):
            raise TypeError("all goals must be Goal objects")

    def add(self, goal: Goal) -> Dict[str, Any]:
        if not isinstance(goal, Goal):
            raise TypeError("goal must be a Goal object")
        self.goals.append(goal)
        return asdict(goal)

    def evaluate(self, telemetry: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not isinstance(telemetry, dict):
            raise TypeError("telemetry must be a dictionary")
        results: List[Dict[str, Any]] = []
        for goal in self.goals:
            observed = telemetry.get(goal.metric)
            row = asdict(goal)
            row.update({"observed": observed, "status": "unknown", "progress": None, "gap": None})
            if isinstance(observed, (int, float)) and observed == observed:
                if goal.target == 0:
                    progress = 1.0 if observed >= 0 else 0.0
                elif goal.target > 0:
                    progress = observed / goal.target
                else:
                    # For negative targets, lower/equal observed values are better.
                    progress = goal.target / observed if observed < 0 else 0.0
                row["progress"] = max(0.0, min(1.0, progress))
                row["gap"] = goal.target - observed
                row["status"] = "achieved" if ((goal.target >= 0 and observed >= goal.target) or (goal.target < 0 and observed <= goal.target)) else "in_progress"
            results.append(row)
        return sorted(results, key=lambda item: (item["status"] == "achieved", -item["priority"], item["name"]))

    def next_priority(self, telemetry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Return the highest-priority unmet goal supported by observed telemetry."""
        evaluated = self.evaluate(telemetry)
        unmet = [row for row in evaluated if row["status"] != "achieved" and row["observed"] is not None]
        return unmet[0] if unmet else None

    def status(self) -> Dict[str, Any]:
        return {"engine": "Cortex Goal Engine", "version": "1.0", "goal_count": len(self.goals)}
