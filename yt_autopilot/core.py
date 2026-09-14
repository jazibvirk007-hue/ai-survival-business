"""Deterministic, rights-first domain primitives for YT Autopilot."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any
import hashlib
import json
import time
import uuid


class RightsStatus(str, Enum):
    VERIFIED_REUSABLE = "VERIFIED_REUSABLE"
    REQUIRES_ATTRIBUTION = "REQUIRES_ATTRIBUTION"
    REQUIRES_PERMISSION = "REQUIRES_PERMISSION"
    UNKNOWN = "UNKNOWN"
    REJECTED = "REJECTED"


class PipelineState(str, Enum):
    IDEA = "IDEA"
    RESEARCH = "RESEARCH"
    TOPIC_SELECTED = "TOPIC_SELECTED"
    MEDIA_SEARCH = "MEDIA_SEARCH"
    RIGHTS_VERIFICATION = "RIGHTS_VERIFICATION"
    MEDIA_ACQUIRED = "MEDIA_ACQUIRED"
    SCRIPT = "SCRIPT"
    FACT_CHECK = "FACT_CHECK"
    VOICE = "VOICE"
    STORYBOARD = "STORYBOARD"
    EDIT_PLAN = "EDIT_PLAN"
    RENDER = "RENDER"
    CAPTIONS = "CAPTIONS"
    THUMBNAIL = "THUMBNAIL"
    SEO = "SEO"
    QC = "QC"
    READY = "READY"
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    ANALYTICS = "ANALYTICS"
    LEARNING = "LEARNING"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class RightsRecord:
    source_url: str
    source_name: str
    creator: str = ""
    license: str = ""
    license_url: str = ""
    usage_restrictions: str = ""
    commercial_use_allowed: bool = False
    modification_allowed: bool = False
    attribution_required: bool = False
    attribution_text: str = ""
    verification_status: RightsStatus = RightsStatus.UNKNOWN
    verified_at: float = field(default_factory=time.time)
    download_date: float | None = None
    evidence: tuple[str, ...] = ()

    def publishable(self) -> bool:
        return self.verification_status in {
            RightsStatus.VERIFIED_REUSABLE,
            RightsStatus.REQUIRES_ATTRIBUTION,
        } and self.commercial_use_allowed and self.modification_allowed


@dataclass
class Asset:
    source_url: str
    source_name: str
    rights: RightsRecord
    creator: str = ""
    local_path: str | None = None
    duration: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    has_audio: bool = False
    sha256: str = ""
    perceptual_hash: str = ""
    topics: list[str] = field(default_factory=list)
    usage_count: int = 0
    asset_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def publishable(self) -> bool:
        return self.rights.publishable()

    def fingerprint(self) -> str:
        payload = f"{self.source_url}|{self.sha256}|{self.duration:.3f}|{self.width}x{self.height}"
        return hashlib.sha256(payload.encode()).hexdigest()


@dataclass(frozen=True)
class TopicScore:
    trend: float
    search_demand: float
    competition: float
    content_gap: float
    evergreen: float
    audience_relevance: float
    footage_availability: float
    production_difficulty: float
    monetization: float

    def final(self) -> float:
        value = (
            0.12 * self.trend + 0.13 * self.search_demand - 0.08 * self.competition
            + 0.10 * self.content_gap + 0.08 * self.evergreen
            + 0.16 * self.audience_relevance + 0.20 * self.footage_availability
            - 0.07 * self.production_difficulty + 0.10 * self.monetization
        )
        return round(max(0.0, min(100.0, value)), 2)


@dataclass(frozen=True)
class ClaimCheck:
    claim_id: str
    text: str
    status: str
    sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class QCReport:
    video_ok: bool
    audio_ok: bool
    captions_ok: bool
    fact_ok: bool
    rights_ok: bool
    metadata_ok: bool
    thumbnail_ok: bool
    errors: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return all((self.video_ok, self.audio_ok, self.captions_ok, self.fact_ok,
                    self.rights_ok, self.metadata_ok, self.thumbnail_ok)) and not self.errors


def rights_gate(assets: list[Asset], music: list[Asset] | None = None) -> tuple[bool, list[str]]:
    """Hard gate: every visual/audio asset needs explicit reusable rights evidence."""
    failures: list[str] = []
    for asset in [*assets, *(music or [])]:
        if not asset.publishable():
            failures.append(f"{asset.asset_id}: rights={asset.rights.verification_status.value}")
        elif not asset.rights.evidence:
            failures.append(f"{asset.asset_id}: rights evidence is missing")
    return not failures, failures


def originality_score(original_narration: float, original_structure: float,
                      editorial_transformation: float, unique_graphics: float,
                      commentary: float) -> float:
    score = (0.25 * original_narration + 0.20 * original_structure +
             0.25 * editorial_transformation + 0.10 * unique_graphics +
             0.20 * commentary)
    return round(max(0.0, min(100.0, score)), 2)


def reused_content_risk(source_footage_pct: float, original_narration: float,
                        transformation: float, source_diversity: float,
                        commentary: float, graphics: float) -> float:
    risk = (0.30 * source_footage_pct + 0.18 * (100 - original_narration) +
            0.20 * (100 - transformation) + 0.10 * (100 - source_diversity) +
            0.15 * (100 - commentary) + 0.07 * (100 - graphics))
    return round(max(0.0, min(100.0, risk)), 2)


def serialise(value: Any) -> str:
    return json.dumps(asdict(value) if hasattr(value, "__dataclass_fields__") else value,
                      default=lambda x: x.value if isinstance(x, Enum) else str(x),
                      sort_keys=True, separators=(",", ":"))
