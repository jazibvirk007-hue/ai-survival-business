"""Framework-neutral live API adapter for the Cortex dashboard.

The adapter keeps dashboard reads and controls attached to one orchestrator
instance. It never exposes credentials or grants direct ledger/outbound access.
"""
from __future__ import annotations

from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from cortex_live_surface import build_live_surface
from cortex_v95_orchestrator import CortexV95Orchestrator

MAX_LIMIT = 50
MAX_BODY_KEYS = 20


def dispatch_dashboard_live(
    method: str,
    path: str,
    *,
    orchestrator: CortexV95Orchestrator,
    payload: Optional[dict[str, Any]] = None,
) -> tuple[int, dict[str, Any]]:
    """Serve bounded dashboard observation/control requests."""
    if not isinstance(orchestrator, CortexV95Orchestrator):
        raise TypeError("orchestrator must be CortexV95Orchestrator")
    payload = {} if payload is None else payload
    if not isinstance(payload, dict):
        return 400, {"ok": False, "error": "payload_must_be_object"}
    if len(payload) > MAX_BODY_KEYS:
        return 400, {"ok": False, "error": "payload_too_large"}

    method = str(method).upper()
    parsed = urlparse(path)
    route = parsed.path
    query = parse_qs(parsed.query)

    if method == "GET" and route == "/api/command-center/live":
        raw_limit = query.get("limit", ["20"])[0]
        try:
            limit = int(raw_limit)
        except (TypeError, ValueError):
            return 400, {"ok": False, "error": "invalid_limit"}
        if not 1 <= limit <= MAX_LIMIT:
            return 400, {"ok": False, "error": "invalid_limit"}
        return 200, {"ok": True, "live": build_live_surface(orchestrator, limit=limit)}

    if method == "GET" and route == "/api/cycles":
        raw_limit = query.get("limit", ["20"])[0]
        try:
            limit = int(raw_limit)
        except (TypeError, ValueError):
            return 400, {"ok": False, "error": "invalid_limit"}
        if not 1 <= limit <= MAX_LIMIT:
            return 400, {"ok": False, "error": "invalid_limit"}
        surface = build_live_surface(orchestrator, limit=limit)
        return 200, {"ok": True, **surface["observability"]["cycles"]}

    return 404, {"ok": False, "error": "not_found"}
