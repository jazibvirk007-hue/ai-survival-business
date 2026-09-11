"""Framework-neutral HTTP routes for the persistent Cortex scheduler."""

from __future__ import annotations

from typing import Any, Optional

from cortex_scheduler_service import CortexSchedulerService

MAX_BODY_KEYS = 10
MAX_APPROVAL_ID = 200
_DEFAULT_SERVICE: Optional[CortexSchedulerService] = None


def _service() -> CortexSchedulerService:
    global _DEFAULT_SERVICE
    if _DEFAULT_SERVICE is None:
        _DEFAULT_SERVICE = CortexSchedulerService()
    return _DEFAULT_SERVICE


def _error(code: str) -> tuple[int, dict[str, Any]]:
    return 400, {"ok": False, "error": code}


def dispatch_scheduler_route(
    method: str,
    path: str,
    *,
    payload: Optional[dict[str, Any]] = None,
    service: Optional[CortexSchedulerService] = None,
) -> tuple[int, dict[str, Any]]:
    """Dispatch bounded scheduler controls without exposing secrets."""
    method = str(method).upper()
    payload = payload or {}
    service = service or _service()

    if method == "GET" and path == "/api/scheduler":
        return 200, {"ok": True, "scheduler": service.snapshot()}

    if method == "POST" and path == "/api/scheduler/pause":
        if payload:
            return _error("unexpected_payload")
        return 200, {"ok": True, "scheduler": service.pause()}

    if method == "POST" and path == "/api/scheduler/resume":
        if payload:
            return _error("unexpected_payload")
        return 200, {"ok": True, "scheduler": service.resume()}

    if method == "POST" and path == "/api/scheduler/tick":
        if len(payload) > MAX_BODY_KEYS:
            return _error("payload_too_large")
        execute = payload.get("execute", False)
        if not isinstance(execute, bool):
            return _error("execute_must_be_boolean")
        approval_id = payload.get("approval_id")
        if approval_id is not None and (not isinstance(approval_id, str) or len(approval_id) > MAX_APPROVAL_ID):
            return _error("invalid_approval_id")
        return 200, service.tick(execute=execute, approval_id=approval_id)

    return 404, {"ok": False, "error": "not_found"}
