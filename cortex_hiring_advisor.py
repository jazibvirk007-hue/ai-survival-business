"""Evidence-based specialist hiring recommendations for Cortex.

This module proposes internal staffing only. It never executes code, grants
permissions, or changes payment/Guard authority.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Mapping

from ai_ceo import ACTIONS
from cortex_specialist_registry import CortexSpecialistRegistry


@dataclass(frozen=True)
class HiringRecommendation:
    action: str
    workload: int
    reason: str
    proposed_name: str
    purpose: str
    execution: str = "not_authorized"


class CortexHiringAdvisor:
    """Convert objective unmet workload into bounded hiring recommendations."""

    MAX_RECOMMENDATIONS = 8
    MAX_WORKLOAD = 1000000

    def __init__(self, registry: CortexSpecialistRegistry) -> None:
        if not isinstance(registry, CortexSpecialistRegistry):
            raise TypeError("registry must be CortexSpecialistRegistry")
        self.registry = registry

    def recommend(self, workload: Mapping[str, Any] | None = None) -> List[Dict[str, Any]]:
        workload = workload or {}
        if not isinstance(workload, Mapping):
            raise TypeError("workload must be a mapping")
        allowed = set(ACTIONS) & set(self.registry.status().get("allowed_actions", []))
        recommendations: List[HiringRecommendation] = []
        for action in ACTIONS:
            if action not in allowed or self.registry.get(action) is not None:
                continue
            raw = workload.get(action, 0)
            try:
                amount = int(raw)
            except (TypeError, ValueError):
                continue
            if amount <= 0:
                continue
            amount = min(amount, self.MAX_WORKLOAD)
            label = action.replace("_", " ").title()
            recommendations.append(HiringRecommendation(
                action=action,
                workload=amount,
                reason=f"Observed unmet workload for {action} requires bounded specialist capacity.",
                proposed_name=f"{label} Specialist",
                purpose=f"Handle bounded {action} workload using existing authorized capabilities.",
            ))
        recommendations.sort(key=lambda item: item.workload, reverse=True)
        return [asdict(item) for item in recommendations[: self.MAX_RECOMMENDATIONS]]

    def status(self) -> Dict[str, Any]:
        return {
            "engine": "Cortex Hiring Advisor",
            "version": "1.0",
            "policy": "evidence_based_non_executing",
            "max_recommendations": self.MAX_RECOMMENDATIONS,
            "execution": "not_authorized",
        }
