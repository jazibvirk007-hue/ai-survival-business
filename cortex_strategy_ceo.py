"""Observed-learning strategy wrapper for the Cortex CEO."""

from __future__ import annotations

from typing import Any, Dict, List

from ai_ceo import AICEO, Decision

MAX_BONUS = 8.0
MAX_PENALTY = 8.0
MIN_OBSERVATIONS = 2


class CortexStrategyCEO(AICEO):
    """Bias deterministic CEO candidates using observed outcome history.

    Learning can influence ranking only. It cannot create actions, change
    approval requirements, authorize execution, or alter financial truth.
    """

    def __init__(self, base: AICEO):
        if not isinstance(base, AICEO):
            raise TypeError("base must be AICEO")
        super().__init__(
            minimum_cash=base.minimum_cash,
            max_actions_per_cycle=base.max_actions_per_cycle,
            ai_runtime=base.ai_runtime,
            ai_selection=base.ai_selection,
            ai_enabled=base.ai_enabled,
        )
        self.history = base.history

    @staticmethod
    def _learning_adjustment(action: str, strategy: List[Dict[str, Any]]) -> float:
        for row in strategy:
            if not isinstance(row, dict) or row.get("action") != action:
                continue
            observed = row.get("observed_outcomes", 0)
            rate = row.get("success_rate")
            if not isinstance(observed, int) or observed < MIN_OBSERVATIONS:
                return 0.0
            if not isinstance(rate, (int, float)) or rate != rate:
                return 0.0
            if rate >= 0.80:
                return MAX_BONUS
            if rate <= 0.30:
                return -MAX_PENALTY
            if rate >= 0.60:
                return 4.0
            if rate <= 0.45:
                return -4.0
            return 0.0
        return 0.0

    def evaluate(self, state: Dict[str, Any]) -> List[Decision]:
        candidates = super().evaluate(state)
        strategy = state.get("memory_strategy", [])
        if not isinstance(strategy, list):
            return candidates

        adjusted: List[Decision] = []
        for decision in candidates:
            adjustment = self._learning_adjustment(decision.action, strategy)
            if adjustment == 0:
                adjusted.append(decision)
                continue
            reason = f"{decision.reason} Observed-learning adjustment: {adjustment:+.0f}; based only on {next((r.get('observed_outcomes', 0) for r in strategy if isinstance(r, dict) and r.get('action') == decision.action), 0)} observed outcomes."
            adjusted.append(
                Decision(
                    action=decision.action,
                    priority=max(0.0, min(100.0, decision.priority + adjustment)),
                    reason=reason,
                    expected_outcome=decision.expected_outcome,
                    requires_approval=decision.requires_approval,
                )
            )
        adjusted.sort(key=lambda item: item.priority, reverse=True)
        return adjusted[: max(1, self.max_actions_per_cycle)]
