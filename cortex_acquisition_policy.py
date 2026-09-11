"""Policy layer for autonomous customer acquisition.

This module scores candidate opportunities without inventing identities or
contact details. Discovery adapters are expected to supply factual records;
this layer decides whether a record is eligible for further qualification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MAX_TEXT = 500
MAX_SCORE = 100


@dataclass(frozen=True)
class AcquisitionDecision:
    eligible: bool
    score: int
    reason: str
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "eligible": self.eligible,
            "score": self.score,
            "reason": self.reason,
            "next_action": self.next_action,
        }


def score_candidate(candidate: dict[str, Any]) -> AcquisitionDecision:
    """Conservatively score a factual prospect record."""
    if not isinstance(candidate, dict):
        return AcquisitionDecision(False, 0, "invalid_candidate", "discard")

    # Never infer identity/contact data from a missing field.
    source = candidate.get("source")
    need = candidate.get("need")
    fit = candidate.get("fit")
    contactable = candidate.get("contactable")

    if not isinstance(source, str) or not source.strip():
        return AcquisitionDecision(False, 0, "missing_source", "discard")
    if not isinstance(need, str) or not need.strip():
        return AcquisitionDecision(False, 0, "missing_verified_need", "qualify")

    # 20 points for a factual source/need record, 60 for fit, 20 for a
    # verified contact path. This gives a true 0..100 scale without changing
    # the eligibility threshold.
    score = 20
    if isinstance(fit, (int, float)) and not isinstance(fit, bool):
        score += max(0, min(60, int(fit)))
    if contactable is True:
        score += 20
    elif contactable is not False:
        score += 5

    score = max(0, min(MAX_SCORE, score))
    if score >= 70 and contactable is True:
        return AcquisitionDecision(True, score, "verified_fit_and_contact_path", "qualify")
    return AcquisitionDecision(False, score, "insufficient_evidence", "research_more")
