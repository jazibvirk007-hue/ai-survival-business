"""Cortex Link policy gate.

Provider/model choice is configuration, not authority. This module gives the CEO
and future agents a single bounded policy check before AI-generated advice can
influence an autonomous cycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

MAX_ADVISORY_TEXT = 6000
ALLOWED_DECISIONS = frozenset({
    "research_market", "create_product", "find_prospects", "qualify_prospects",
    "draft_outreach", "follow_up", "review_financials", "improve_offer", "rest_and_observe",
})


@dataclass(frozen=True)
class AdvisoryResult:
    action: str
    score: int
    reason: str
    accepted: bool


def validate_advisory(payload: Mapping[str, Any], candidates: Sequence[str]) -> AdvisoryResult:
    if not isinstance(payload, Mapping):
        return AdvisoryResult("", 0, "invalid advisory payload", False)
    action = payload.get("action")
    if not isinstance(action, str):
        return AdvisoryResult("", 0, "missing advisory action", False)
    action = action.strip()
    allowed = set(candidates) & ALLOWED_DECISIONS
    if action not in allowed:
        return AdvisoryResult(action, 0, "advisory action is outside the deterministic candidate set", False)
    try:
        score = int(payload.get("score", 0))
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(100, score))
    reason = str(payload.get("reason", ""))[:MAX_ADVISORY_TEXT]
    return AdvisoryResult(action, score, reason, True)


def advisory_prompt(candidates: Sequence[Mapping[str, Any]]) -> str:
    """Create a compact prompt containing only deterministic candidates."""
    rows = []
    for item in candidates:
        if not isinstance(item, Mapping):
            continue
        action = str(item.get("action", ""))[:80]
        priority = str(item.get("priority", 0))[:20]
        reason = str(item.get("reason", ""))[:400]
        if action:
            rows.append(f"- {action} | deterministic_priority={priority} | {reason}")
    return (
        "Choose only one action from the candidates below. Do not invent an action. "
        "Return JSON: {\"action\": string, \"score\": integer 0-100, \"reason\": string}.\n"
        + "\n".join(rows)
    )
