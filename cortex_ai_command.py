"""Cortex Link command surface for provider/model control.

This module is deliberately framework-free so the existing Command Center can
mount it without adding dependencies. It exposes browser-safe payload builders
and keeps credentials inside the server-side AI runtime.
"""

from __future__ import annotations

from typing import Any, Mapping

from cortex_ai_control import AIControlSelection, discover_models, safe_provider_catalog, safe_selection_status, save_selection
from cortex_ai_runtime import CortexAIRuntime


class CortexAICommand:
    """Safe application service for the Cortex Link UI."""

    def __init__(self, *, runtime: CortexAIRuntime | None = None, selection_path: str = "cortex_ai_selection.json") -> None:
        self.runtime = runtime or CortexAIRuntime()
        self.selection_path = selection_path

    def catalog(self) -> dict[str, Any]:
        return {"providers": safe_provider_catalog()}

    def selected(self) -> dict[str, Any]:
        return safe_selection_status(self.runtime, self.selection_path)

    def models(self, provider_id: str) -> dict[str, Any]:
        return {"provider_id": provider_id, "models": discover_models(self.runtime, provider_id)}

    def select(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            raise ValueError("selection payload must be an object")
        provider_id = payload.get("provider_id")
        model = payload.get("model")
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ValueError("provider_id is required")
        if not isinstance(model, str) or not model.strip() or len(model.strip()) > 200:
            raise ValueError("model is required and must be <= 200 characters")
        selection = AIControlSelection(provider_id.strip(), model.strip())
        save_selection(selection, self.selection_path)
        return self.selected()

    def connection_test(self) -> dict[str, Any]:
        status = self.selected()
        if not status.get("selected"):
            return {"ok": False, "error": "no AI provider/model selected"}
        if not status.get("configured"):
            return {"ok": False, "error": "server-side provider credential is not configured"}
        try:
            self.runtime.generate(
                AIControlSelection(status["provider_id"], status["model"]).to_runtime(),
                [{"role": "user", "content": "Respond with exactly: CORTEX_CONNECTION_OK"}],
                temperature=0,
            )
        except Exception:
            return {"ok": False, "error": "AI provider connection failed"}
        return {"ok": True, "provider_id": status["provider_id"], "model": status["model"]}
