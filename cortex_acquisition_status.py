"""Browser-safe acquisition pipeline status for Cortex Command Center."""

from __future__ import annotations

from typing import Any, Iterable, Optional

from cortex_acquisition_pipeline import CortexAcquisitionPipeline

MAX_RECORDS = 50


def build_acquisition_snapshot(
    records: Optional[Iterable[dict[str, Any]]] = None,
    *,
    pipeline: Optional[CortexAcquisitionPipeline] = None,
) -> dict[str, Any]:
    """Expose bounded acquisition planning state without executing outreach."""
    pipeline = pipeline or CortexAcquisitionPipeline()
    snapshot: dict[str, Any] = {
        "engine": "Cortex Acquisition Pipeline",
        "version": "1.0",
        "status": "READY" if records is not None else "WAITING_FOR_AUTHORIZED_SOURCE",
        "execution": "planning_only",
        "outbound": "Cortex Communications + Cortex Guard",
        "truth_policy": "no_invented_customers_or_revenue",
    }
    if records is None:
        snapshot["queue"] = []
        snapshot["eligible_count"] = 0
        return snapshot
    try:
        items = list(records)
        if len(items) > MAX_RECORDS:
            raise ValueError("too_many_records")
        result = pipeline.plan(items, limit=min(20, max(1, len(items)))) if items else pipeline.plan([], limit=1)
        snapshot["eligible_count"] = result.get("eligible_count", 0)
        snapshot["reviewed_count"] = result.get("total_reviewed", 0)
        snapshot["queue"] = result.get("candidates", [])[:20]
    except Exception:
        snapshot["status"] = "DEGRADED"
        snapshot["eligible_count"] = 0
        snapshot["reviewed_count"] = 0
        snapshot["queue"] = []
    return snapshot
