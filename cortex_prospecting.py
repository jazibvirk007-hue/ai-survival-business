"""Cortex Prospecting Engine: discover and qualify real customer opportunities.

This module plans customer discovery from supplied, authorized sources. It does
not scrape private data, invent contacts, send spam, or contact anyone itself.
Connectors can later supply public/consented records; outbound communication
remains behind Cortex Communications + Cortex Guard.
"""

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Dict, Iterable, List


@dataclass(frozen=True)
class Prospect:
    name: str
    source: str
    problem_signal: str
    fit_score: float
    intent_score: float = 0.0
    contactability: float = 0.0
    consent_or_basis: str = "public_business_contact"
    status: str = "discovered"

    def __post_init__(self) -> None:
        for field in ("name", "source", "problem_signal", "consent_or_basis", "status"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be non-empty")
        for field in ("fit_score", "intent_score", "contactability"):
            value = getattr(self, field)
            if not isinstance(value, (int, float)) or not isfinite(float(value)) or not 0 <= value <= 100:
                raise ValueError(f"{field} must be between 0 and 100")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CortexProspecting:
    """Score supplied prospect records using transparent, bounded signals."""

    @staticmethod
    def discover(records: Iterable[Dict[str, Any]]) -> List[Prospect]:
        if records is None:
            raise TypeError("records are required")
        prospects: List[Prospect] = []
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("each prospect record must be a dictionary")
            prospects.append(Prospect(
                name=record.get("name", ""),
                source=record.get("source", ""),
                problem_signal=record.get("problem_signal", ""),
                fit_score=record.get("fit_score", 0),
                intent_score=record.get("intent_score", 0),
                contactability=record.get("contactability", 0),
                consent_or_basis=record.get("consent_or_basis", "public_business_contact"),
                status=record.get("status", "discovered"),
            ))
        return prospects

    @staticmethod
    def rank(prospects: Iterable[Prospect]) -> List[Dict[str, Any]]:
        items = list(prospects)
        if any(not isinstance(item, Prospect) for item in items):
            raise TypeError("all prospects must be Prospect objects")
        ranked = []
        for prospect in items:
            # Intent and fit dominate; contactability only breaks ties modestly.
            score = (prospect.fit_score * 0.45) + (prospect.intent_score * 0.45) + (prospect.contactability * 0.10)
            row = prospect.to_dict()
            row["priority_score"] = round(score, 2)
            row["recommended_action"] = "prepare_personalized_outreach" if score >= 60 else "observe_or_research"
            row["requires_guard"] = True
            ranked.append(row)
        return sorted(ranked, key=lambda row: row["priority_score"], reverse=True)

    @staticmethod
    def next_actions(ranked: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        if not isinstance(ranked, list) or not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
            raise ValueError("ranked must be a list and limit must be 1..50")
        return [{
            "action": row["recommended_action"],
            "prospect": row["name"],
            "source": row["source"],
            "reason": "highest observed fit/intent among supplied prospects",
            "requires_approval": True,
        } for row in ranked[:limit] if isinstance(row, dict) and row.get("name")]

    def status(self) -> Dict[str, Any]:
        return {
            "engine": "Cortex Prospecting Engine",
            "version": "1.0",
            "discovery": "authorized_sources_only",
            "outbound": "Cortex Communications + Guard",
            "policy": "no_private_data_scraping_or_unsolicited_spam",
        }
