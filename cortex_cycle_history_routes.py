"""Framework-neutral HTTP route for bounded Cortex cycle history."""
from __future__ import annotations

from typing import Any, Mapping, Optional

from cortex_autonomy_runtime import CortexAutonomyRuntime
from cortex_cycle_history import build_cycle_history

MAX_LIMIT = 50


def dispatch_cycle_history_route(
    method: str,
    path: str,
    *,
    runtime: Optional[CortexAutonomyRuntime] = None,
    runtime_snapshot: Optional[Mapping[str, Any]] = None,
) -> tuple[int, dict[str, Any]]:
    if str(method).upper() != "GET" or path.split("?", 1)[0] != "/api/cycles":
        return 404, {"ok": False, "error": "not_found"}
    query = path.split("?", 1)[1] if "?" in path else ""
    limit = 20
    for part in query.split("&"):
        if part.startswith("limit="):
            try:
                limit = int(part[6:])
            except ValueError:
                return 400, {"ok": False, "error": "invalid_limit"}
    if not 1 <= limit <= MAX_LIMIT:
        return 400, {"ok": False, "error": "invalid_limit"}
    if runtime_snapshot is None:
        runtime = runtime or CortexAutonomyRuntime()
        runtime_snapshot = runtime.snapshot()
    return 200, {"ok": True, **build_cycle_history(runtime_snapshot, limit)}
