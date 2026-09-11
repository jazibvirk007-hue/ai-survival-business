"""Cortex Social Sources: governed social-media prospect discovery.

This layer normalizes prospect signals supplied by official APIs, approved
connectors, or public pages. It never bypasses authentication, scrapes private
accounts, harvests passwords, or sends unsolicited messages.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List
from urllib.parse import urlparse


SUPPORTED_PLATFORMS = {
    "linkedin", "instagram", "facebook", "tiktok", "x", "youtube",
    "reddit", "threads"
}


@dataclass(frozen=True)
class SocialProspectSignal:
    platform: str
    profile_or_post_url: str
    display_name: str
    need_signal: str
    relevance_score: float = 0.0
    intent_score: float = 0.0
    contactability: float = 0.0
    access_basis: str = "official_api_or_public_page"

    def __post_init__(self) -> None:
        if self.platform not in SUPPORTED_PLATFORMS:
            raise ValueError("unsupported social platform")
        if not self.display_name.strip() or not self.need_signal.strip():
            raise ValueError("display_name and need_signal are required")
        parsed = urlparse(self.profile_or_post_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("profile_or_post_url must be an HTTPS URL")
        for value in (self.relevance_score, self.intent_score, self.contactability):
            if not isinstance(value, (int, float)) or not 0 <= float(value) <= 100:
                raise ValueError("scores must be between 0 and 100")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CortexSocialSources:
    """Normalize and rank social signals without performing outbound contact."""

    @staticmethod
    def ingest(records: Iterable[Dict[str, Any]]) -> List[SocialProspectSignal]:
        if records is None:
            raise TypeError("records are required")
        return [SocialProspectSignal(**record) for record in records]

    @staticmethod
    def rank(signals: Iterable[SocialProspectSignal]) -> List[Dict[str, Any]]:
        rows = []
        for signal in signals:
            score = (signal.relevance_score * 0.40) + (signal.intent_score * 0.45) + (signal.contactability * 0.15)
            row = signal.to_dict()
            row["priority_score"] = round(score, 2)
            row["recommended_action"] = "research_and_prepare_personalized_outreach" if score >= 60 else "observe"
            row["requires_guard"] = True
            rows.append(row)
        return sorted(rows, key=lambda row: row["priority_score"], reverse=True)

    @staticmethod
    def status() -> Dict[str, Any]:
        return {
            "engine": "Cortex Social Sources",
            "platforms": sorted(SUPPORTED_PLATFORMS),
            "discovery": "official_apis_or_public_pages",
            "private_account_access": False,
            "credential_harvesting": False,
            "automated_outreach": "Cortex Communications + Cortex Guard",
            "policy": "platform_terms_and_anti_spam_controls_required",
        }
