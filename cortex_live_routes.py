"""Read-only HTTP routes for live Cortex observability."""
from __future__ import annotations

from typing import Any, Mapping, Optional
from urllib.parse import parse_qs, urlparse

from cortex_live_observability import build_live_observability

MAX_LIMIT = 50


def dispatch_live_route(
    method: str,
    path: str,
    *,
    runtime_snapshot: Optional[Mapping[str, Any]] = None,
) -> tuple[int, dict[str, Any]]:
    """Expose bounded live telemetry without granting execution authority."""
    if str(method).upper() != "GET":
        return 405, {"ok": False, "error": "method_not_allowed"}
    parsed = urlparse(path)
    if parsed.path != "/api/command-center/live":
        return 404, {"ok": False, "error": "not_found"}
    if runtime_snapshot is None:
        return 503, {"ok": False, "error": "runtime_snapshot_unavailable"}
    raw_limit = parse_qs(parsed.query).get("limit", ["20"])[0]
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        return 400, {"ok": False, "error": "invalid_limit"}
    if not 1 <= limit <= MAX_LIMIT:
        return 400, {"ok": False, "error": "invalid_limit"}
    try:
        snapshot = build_live_observability(runtime_snapshot, limit=limit)
    except ValueError:
        return 400, {"ok": False, "error": "invalid_limit"}
    except Exception:
        return 503, {"ok": False, "error": "live_observability_unavailable"}
    return 200, {"ok": True, **snapshot}
