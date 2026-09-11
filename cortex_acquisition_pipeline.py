"""Unified customer-acquisition planning pipeline for Cortex.

This layer joins factual prospect discovery, prospect ranking, and the
conservative acquisition policy. It prepares a bounded queue for the
Autonomous Growth Loop; it never invents identities, contact details,
customer intent, consent, replies, conversions, or revenue, and it never
sends outbound communication.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from cortex_acquisition_policy import AcquisitionDecision, score_candidate
from cortex_prospecting import CortexProspecting

MAX_RECORDS = 50
MAX_RESULTS = 20


def _bounded_records(records: Iterable[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    if isinstance(records, (str, bytes)) or records is None:
        raise TypeError("records must be an iterable of dictionaries")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_RESULTS:
        raise ValueError(f"limit must be between 1 and {MAX_RESULTS}")
    items = list(records)
    if len(items) > MAX_RECORDS:
        raise ValueError(f"at most {MAX_RECORDS} records are supported")
    if any(not isinstance(item, dict) for item in items):
        raise ValueError("each record must be a dictionary")
    return items


def _policy_candidate(row: Dict[str, Any]) -> Dict[str, Any]:
    """Map only observed prospect signals into the acquisition policy."""
    basis = row.get("consent_or_basis")
    contactability = row.get("contactability")
    return {
        "source": row.get("source"),
        "need": row.get("problem_signal"),
        "fit": row.get("fit_score"),
        # A usable contact path requires both a strong observed contactability
        # signal and an explicit lawful/authorized basis in the source record.
        "contactable": (
            isinstance(contactability, (int, float))
            and not isinstance(contactability, bool)
            and contactability >= 60
            and isinstance(basis, str)
            and bool(basis.strip())
        ),
    }


def _decision_view(row: Dict[str, Any], decision: AcquisitionDecision) -> Dict[str, Any]:
    return {
        "name": str(row.get("name", ""))[:200],
        "source": str(row.get("source", ""))[:500],
        "problem_signal": str(row.get("problem_signal", ""))[:500],
        "fit_score": row.get("fit_score"),
        "intent_score": row.get("intent_score"),
        "contactability": row.get("contactability"),
        "consent_or_basis": str(row.get("consent_or_basis", ""))[:300],
        "priority_score": row.get("priority_score", 0),
        "recommended_action": row.get("recommended_action", "observe_or_research"),
        "requires_guard": True,
        **decision.to_dict(),
    }


class CortexAcquisitionPipeline:
    """Prepare the highest-quality factual acquisition opportunities."""

    def __init__(self, *, prospecting: CortexProspecting | None = None) -> None:
        self.prospecting = prospecting or CortexProspecting()
        if not isinstance(self.prospecting, CortexProspecting):
            raise TypeError("prospecting must be CortexProspecting")

    def plan(self, records: Iterable[Dict[str, Any]], *, limit: int = 20) -> Dict[str, Any]:
        """Return a bounded, policy-checked acquisition queue."""
        items = _bounded_records(records, limit)
        prospects = self.prospecting.discover(items)
        ranked = self.prospecting.rank(prospects)

        reviewed: List[Dict[str, Any]] = []
        for row in ranked:
            decision = score_candidate(_policy_candidate(row))
            reviewed.append(_decision_view(row, decision))

        eligible = [row for row in reviewed if row["eligible"]]
        eligible.sort(key=lambda row: (row["score"], row["priority_score"]), reverse=True)
        return {
            "success": True,
            "observed": "acquisition_plan",
            "source_policy": "authorized_sources_only",
            "outbound_policy": "Cortex Communications + Guard",
            "total_reviewed": len(reviewed),
            "eligible_count": len(eligible),
            "candidates": eligible[:limit],
            "reviewed": reviewed[:limit],
        }

    def status(self) -> Dict[str, Any]:
        return {
            "engine": "Cortex Acquisition Pipeline",
            "version": "1.0",
            "discovery": "authorized_sources_only",
            "policy": "factual_need_fit_contactability_and_basis",
            "outbound": "Cortex Communications + Cortex Guard",
            "execution": "planning_only",
            "truth_policy": "no_invented_customers_or_revenue",
        }
