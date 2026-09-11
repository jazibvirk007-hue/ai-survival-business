"""Controlled business experiments for TJ Cortex.

Experiments compare observed outcomes against explicit hypotheses. This module
never fabricates results and never executes external actions by itself.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Experiment:
    name: str
    hypothesis: str
    metric: str
    baseline: float
    target: float
    direction: str = "increase"

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("experiment name must be non-empty")
        if not isinstance(self.hypothesis, str) or not self.hypothesis.strip():
            raise ValueError("hypothesis must be non-empty")
        if not isinstance(self.metric, str) or not self.metric.strip():
            raise ValueError("metric must be non-empty")
        if not isinstance(self.baseline, (int, float)) or not isinstance(self.target, (int, float)):
            raise ValueError("baseline and target must be numeric")
        if direction not in ("increase", "decrease"):
            raise ValueError("direction must be increase or decrease")


class CortexExperimentEngine:
    """Track experiment hypotheses and evaluate only observed outcomes."""

    def __init__(self) -> None:
        self.experiments: List[Dict[str, Any]] = []

    def create(self, experiment: Experiment) -> Dict[str, Any]:
        if not isinstance(experiment, Experiment):
            raise TypeError("experiment must be an Experiment object")
        record = asdict(experiment)
        record.update({"status": "running", "observed": None, "result": "awaiting_observation"})
        self.experiments.append(record)
        return dict(record)

    def evaluate(self, name: str, observed: float) -> Dict[str, Any]:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("experiment name must be non-empty")
        if not isinstance(observed, (int, float)):
            raise ValueError("observed must be numeric")
        for record in reversed(self.experiments):
            if record["name"] == name and record["status"] == "running":
                record["observed"] = float(observed)
                target = record["target"]
                direction = record["direction"]
                record["status"] = "completed"
                record["result"] = "winner" if ((direction == "increase" and observed >= target) or (direction == "decrease" and observed <= target)) else "loser"
                return dict(record)
        raise KeyError("running experiment not found")

    def pending(self) -> List[Dict[str, Any]]:
        return [dict(item) for item in self.experiments if item["status"] == "running"]

    def latest(self, limit: int = 10) -> List[Dict[str, Any]]:
        if not isinstance(limit, int) or limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        return [dict(item) for item in self.experiments[-limit:]]

    def status(self) -> Dict[str, Any]:
        return {
            "engine": "Cortex Experiment Engine",
            "version": "1.0",
            "total": len(self.experiments),
            "running": len(self.pending()),
            "completed": sum(item["status"] == "completed" for item in self.experiments),
        }
