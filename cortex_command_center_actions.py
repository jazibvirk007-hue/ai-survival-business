"""Governed action facade for Cortex Command Center.

The dashboard should call this module instead of manipulating provider
configuration directly. Selection is validated by Cortex Link and connection
tests are explicit. No credential values cross this boundary.
"""

from __future__ import annotations

from typing import Any, Optional

from cortex_ai_command import CortexAICommand

MAX_MODEL_LENGTH = 200


def select_provider(
    payload: dict[str, Any],
    *,
    command: Optional[CortexAICommand] = None,
) -> dict[str, Any]:
    """Validate and persist a governed provider/model selection."""
    if not isinstance(payload, dict):
        return {"ok": False, "error": "invalid_payload"}
    provider_id = payload.get("provider_id")
    model = payload.get("model")
    if not isinstance(provider_id, str) or not provider_id.strip():
        return {"ok": False, "error": "provider_required"}
    if not isinstance(model, str) or not model.strip():
        return {"ok": False, "error": "model_required"}
    if len(model) > MAX_MODEL_LENGTH:
        return {"ok": False, "error": "model_too_long"}

    command = command or CortexAICommand()
    try:
        result = command.select({"provider_id": provider_id.strip(), "model": model.strip()})
    except Exception:
        return {"ok": False, "error": "selection_failed"}
    return {"ok": True, "selection": result}


def test_provider(*, command: Optional[CortexAICommand] = None) -> dict[str, Any]:
    """Run the explicit provider connectivity check."""
    command = command or CortexAICommand()
    try:
        result = command.connection_test()
    except Exception:
        return {"ok": False, "error": "connection_test_failed"}
    return {
        "ok": bool(result.get("ok")),
        "provider_id": result.get("provider_id", ""),
        "model": result.get("model", ""),
        "error": result.get("error", "") if not result.get("ok") else "",
    }
