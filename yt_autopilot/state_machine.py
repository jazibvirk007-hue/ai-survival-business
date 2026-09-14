"""Persistable pipeline state transitions with fail-closed rules."""
from dataclasses import dataclass
from enum import Enum
from .core import PipelineState


ALLOWED: dict[PipelineState, set[PipelineState]] = {
    PipelineState.IDEA: {PipelineState.RESEARCH},
    PipelineState.RESEARCH: {PipelineState.TOPIC_SELECTED, PipelineState.BLOCKED},
    PipelineState.TOPIC_SELECTED: {PipelineState.MEDIA_SEARCH},
    PipelineState.MEDIA_SEARCH: {PipelineState.RIGHTS_VERIFICATION, PipelineState.BLOCKED},
    PipelineState.RIGHTS_VERIFICATION: {PipelineState.MEDIA_ACQUIRED, PipelineState.BLOCKED},
    PipelineState.MEDIA_ACQUIRED: {PipelineState.SCRIPT, PipelineState.MEDIA_SEARCH},
    PipelineState.SCRIPT: {PipelineState.FACT_CHECK, PipelineState.BLOCKED},
    PipelineState.FACT_CHECK: {PipelineState.VOICE, PipelineState.SCRIPT, PipelineState.BLOCKED},
    PipelineState.VOICE: {PipelineState.STORYBOARD, PipelineState.BLOCKED},
    PipelineState.STORYBOARD: {PipelineState.EDIT_PLAN},
    PipelineState.EDIT_PLAN: {PipelineState.RENDER, PipelineState.BLOCKED},
    PipelineState.RENDER: {PipelineState.CAPTIONS, PipelineState.EDIT_PLAN, PipelineState.BLOCKED},
    PipelineState.CAPTIONS: {PipelineState.THUMBNAIL, PipelineState.BLOCKED},
    PipelineState.THUMBNAIL: {PipelineState.SEO, PipelineState.BLOCKED},
    PipelineState.SEO: {PipelineState.QC, PipelineState.BLOCKED},
    PipelineState.QC: {PipelineState.READY, PipelineState.BLOCKED},
    PipelineState.READY: {PipelineState.SCHEDULED, PipelineState.PUBLISHED, PipelineState.BLOCKED},
    PipelineState.SCHEDULED: {PipelineState.PUBLISHED, PipelineState.BLOCKED},
    PipelineState.PUBLISHED: {PipelineState.ANALYTICS},
    PipelineState.ANALYTICS: {PipelineState.LEARNING},
    PipelineState.LEARNING: {PipelineState.RESEARCH},
    PipelineState.BLOCKED: {PipelineState.RESEARCH},
}


@dataclass
class Pipeline:
    state: PipelineState = PipelineState.IDEA

    def transition(self, target: PipelineState) -> None:
        if target not in ALLOWED.get(self.state, set()):
            raise ValueError(f"Illegal pipeline transition: {self.state} -> {target}")
        self.state = target

    def can_publish(self) -> bool:
        return self.state == PipelineState.READY
