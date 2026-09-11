"""Operational health summary for Cortex AI Link.

This is intentionally conservative: configured means credentials/config exist;
ready also requires successful provider connectivity. No secret values are
returned.
"""

from __future__ import annotations

from typing import Any, Optional

from cortex_ai_command import CortexAICommand


def build_ai_health(command: Optional[CortexAICommand] = None) -> dict[str, Any]:
    command = command or CortexAICommand()
    selected = command.selected()
    if not selected.get("selected"):
        return {"status": "NOT_CONFIGURED", "selected": False, "connected": False}

    test = command.connection_test()
    connected = bool(test.get("ok"))
    return {
        "status": "READY" if connected else "DEGRADED",
        "selected": True,
        "connected": connected,
        "provider_id": selected.get("provider_id", ""),
        "model": selected.get("model", ""),
        "message": "provider reachable" if connected else "provider unavailable or not configured",
    }
