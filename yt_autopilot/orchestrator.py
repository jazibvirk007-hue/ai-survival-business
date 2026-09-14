"""Bounded orchestration skeleton for the autonomous production loop.

The orchestrator coordinates trusted callables; it never grants an LLM arbitrary tool access.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Any
from .core import PipelineState, Asset, rights_gate
from .state_machine import Pipeline


@dataclass(frozen=True)
class RunLimits:
    max_retries_per_job: int = 2
    max_assets: int = 80
    max_daily_videos: int = 1
    max_video_cost: float = 5.0


@dataclass
class ProductionContext:
    pipeline: Pipeline
    assets: list[Asset]
    data: dict[str, Any]


class AutopilotOrchestrator:
    """Fail-closed coordinator for one video production run."""

    def __init__(self, *, limits: RunLimits | None = None, publishing_enabled: bool = False):
        self.limits = limits or RunLimits()
        self.publishing_enabled = publishing_enabled
        self.stop_publishing = False

    def run_until_qc(self, ctx: ProductionContext, jobs: dict[str, Callable[[ProductionContext], None]]) -> ProductionContext:
        sequence = [
            (PipelineState.RESEARCH, "research"),
            (PipelineState.TOPIC_SELECTED, "select_topic"),
            (PipelineState.MEDIA_SEARCH, "discover_assets"),
            (PipelineState.RIGHTS_VERIFICATION, "verify_rights"),
            (PipelineState.MEDIA_ACQUIRED, "acquire_assets"),
            (PipelineState.SCRIPT, "write_script"),
            (PipelineState.FACT_CHECK, "fact_check"),
            (PipelineState.VOICE, "generate_voice"),
            (PipelineState.STORYBOARD, "storyboard"),
            (PipelineState.EDIT_PLAN, "edit_plan"),
            (PipelineState.RENDER, "render"),
            (PipelineState.CAPTIONS, "captions"),
            (PipelineState.THUMBNAIL, "thumbnail"),
            (PipelineState.SEO, "seo"),
            (PipelineState.QC, "quality_check"),
        ]
        for state, job_name in sequence:
            ctx.pipeline.transition(state)
            job = jobs.get(job_name)
            if job is None:
                ctx.pipeline.transition(PipelineState.BLOCKED)
                raise RuntimeError(f"Missing trusted job handler: {job_name}")
            job(ctx)
            if state == PipelineState.RIGHTS_VERIFICATION:
                ok, failures = rights_gate(ctx.assets)
                if not ok:
                    ctx.data["rights_failures"] = failures
                    ctx.pipeline.transition(PipelineState.BLOCKED)
                    raise PermissionError("Rights gate blocked production")
        return ctx

    def authorize_publish(self, ctx: ProductionContext) -> None:
        if self.stop_publishing or not self.publishing_enabled:
            raise PermissionError("Publishing is disabled or emergency-stopped")
        if ctx.pipeline.state != PipelineState.READY:
            raise PermissionError(f"Video is not READY: {ctx.pipeline.state}")
        ok, failures = rights_gate(ctx.assets)
        if not ok:
            raise PermissionError(f"Rights gate failed: {failures}")
