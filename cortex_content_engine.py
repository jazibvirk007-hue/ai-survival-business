"""Cortex Content Engine: create governed articles and social engagement drafts.

Content creation is separated from publishing. Publishing/replies require a
connected platform adapter and Cortex Guard approval according to policy.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


CONTENT_TYPES = ("article", "social_post", "comment_reply")
PLATFORMS = ("linkedin", "instagram", "facebook", "tiktok", "x", "youtube", "reddit", "threads")


@dataclass(frozen=True)
class ContentDraft:
    content_type: str
    platform: str
    topic: str
    body: str
    purpose: str
    requires_approval: bool = True

    def __post_init__(self) -> None:
        if self.content_type not in CONTENT_TYPES:
            raise ValueError("unsupported content type")
        if self.platform not in PLATFORMS:
            raise ValueError("unsupported platform")
        for field in ("topic", "body", "purpose"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be non-empty")
        if len(self.body) > 30000:
            raise ValueError("body is too long")
        if not isinstance(self.requires_approval, bool):
            raise ValueError("requires_approval must be boolean")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CortexContentEngine:
    """Prepare useful, non-spam content and governed engagement actions."""

    def __init__(self) -> None:
        self._drafts: List[ContentDraft] = []

    def create_draft(self, content_type: str, platform: str, topic: str, body: str, purpose: str) -> ContentDraft:
        draft = ContentDraft(content_type, platform, topic, body, purpose, True)
        self._drafts.append(draft)
        return draft

    def plan_comment(self, platform: str, topic: str, body: str, purpose: str) -> ContentDraft:
        return self.create_draft("comment_reply", platform, topic, body, purpose)

    def plan_article(self, platform: str, topic: str, body: str, purpose: str) -> ContentDraft:
        return self.create_draft("article", platform, topic, body, purpose)

    def pending(self) -> List[Dict[str, Any]]:
        return [draft.to_dict() for draft in self._drafts]

    def next_actions(self, limit: int = 10) -> List[Dict[str, Any]]:
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
            raise ValueError("limit must be 1..50")
        return [{
            "action": "publish_content",
            "platform": draft.platform,
            "content_type": draft.content_type,
            "topic": draft.topic,
            "requires_approval": True,
            "reason": draft.purpose,
        } for draft in self._drafts[:limit]]

    def status(self) -> Dict[str, Any]:
        return {
            "engine": "Cortex Content Engine",
            "version": "1.0",
            "content_types": list(CONTENT_TYPES),
            "platforms": list(PLATFORMS),
            "publishing": "adapter_required",
            "engagement_policy": "relevant_conversation_only",
            "spam": "prohibited",
            "approval": "Cortex Guard required",
        }
