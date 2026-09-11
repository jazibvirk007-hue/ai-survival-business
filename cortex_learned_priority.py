"""Bounded learning adjustment for AI CEO priorities."""

from __future__ import annotations

from typing import Any, Iterable

MAX_BONUS = 10.0
MIN_OBSERVATIONS = 2


def learned_priority_adjustment(action: str, observations: Iterable[dict[str, Any]]) -> float:
    """Return a small evidence-weighted adjustment in [-10, +10]."""
    if not isinstance(action, str) or not action or len(action) > 200:
        return 0.0
    successes = failures = 0
    for row in observations:
        if not isinstance(row, dict) or row.get("action") != action:
            continue
        try:
            successes += int(row.get("successes", 0))
            failures += int(row.get("failures", 0))
        except (TypeError, ValueError):
            continue
    total = successes + failures
    if total < MIN_OBSERVATIONS:
        return 0.0
    rate = successes / total
    # 50% is neutral; adjustment reaches +/-10 only at 0% or 100% success.
    return max(-MAX_BONUS, min(MAX_BONUS, (rate - 0.5) * 20.0))


def apply_learned_priorities(candidates: list[Any], observations: Iterable[dict[str, Any]]) -> list[Any]:
    """Return candidates with bounded learned adjustments, preserving policy flags."""
    from dataclasses import replace

    result = []
    for candidate in candidates:
        bonus = learned_priority_adjustment(candidate.action, observations)
        if bonus:
            result.append(replace(candidate, priority=max(0.0, min(100.0, candidate.priority + bonus))))
        else:
            result.append(candidate)
    return sorted(result, key=lambda item: item.priority, reverse=True)
