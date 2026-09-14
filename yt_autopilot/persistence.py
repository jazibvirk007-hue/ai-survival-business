"""Database-independent persistence contracts for YT Autopilot."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    job_type: str
    channel_id: str
    idempotency_key: str
    status: str = "QUEUED"
    attempts: int = 0


class JobStore(Protocol):
    def enqueue(self, job: JobRecord) -> JobRecord: ...
    def get(self, job_id: str) -> JobRecord | None: ...
    def mark_running(self, job_id: str) -> JobRecord: ...
    def mark_finished(self, job_id: str) -> JobRecord: ...
    def mark_failed(self, job_id: str, error: str) -> JobRecord: ...


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def job_payload(job: JobRecord, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "job_type": job.job_type,
        "channel_id": job.channel_id,
        "idempotency_key": job.idempotency_key,
        "status": job.status,
        "attempts": job.attempts,
        "payload": payload or {},
        "created_at": utc_now().isoformat(),
    }
