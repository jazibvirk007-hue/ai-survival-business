"""Framework-free HTTP-facing Cortex Link API service.

The dashboard can delegate provider/model control here without exposing secrets.
All failures are converted to bounded, browser-safe response objects.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from cortex_ai_command import CortexAICommand

MAX_PROVIDER_ID = 100
MAX_MODEL_ID = 200


class CortexLinkAPI:
    def __init__(self, *, command: Optional[CortexAICommand] = None) -> None:
        self.command = command or CortexAICommand()

    def get_catalog(self) -> dict[str, Any]:
        return self.command.catalog()

    def get_selected(self) -> dict[str, Any]:
        return self.command.selected()

    def get_models(self, provider_id: str) -> dict[str, Any]:
        if not isinstance(provider_id, str) or not provider_id.strip() or len(provider_id) > MAX_PROVIDER_ID:
            return {"ok": False, "error": "invalid provider_id"}
        try:
            result = self.command.models(provider_id.strip())
            return {"ok": True, "provider_id": provider_id.strip(), "models": result.get("models", [])[:200]}
        except Exception:
            return {"ok": False, "error": "model discovery failed"}

    def post_select(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            return {"ok": False, "error": "selection must be an object"}
        provider_id = payload.get("provider_id")
        model = payload.get("model")
        if not isinstance(provider_id, str) or not provider_id.strip() or len(provider_id) > MAX_PROVIDER_ID:
            return {"ok": False, "error": "invalid provider_id"}
        if not isinstance(model, str) or not model.strip() or len(model) > MAX_MODEL_ID:
            return {"ok": False, "error": "invalid model"}
        try:
            selected = self.command.select({"provider_id": provider_id.strip(), "model": model.strip()})
            return {"ok": True, **selected}
        except Exception:
            return {"ok": False, "error": "provider/model selection failed"}

    def post_connection_test(self) -> dict[str, Any]:
        try:
            return self.command.connection_test()
        except Exception:
            return {"ok": False, "error": "AI provider connection failed"}

    def handle(self, method: str, path: str, payload: Optional[Mapping[str, Any]] = None, *, provider_id: Optional[str] = None) -> tuple[int, dict[str, Any]]:
        """Route only the Cortex Link API surface; never accept credentials."""
        method = str(method).upper()
        path = str(path)
        if method == "GET" and path == "/api/ai/catalog":
            return 200, self.get_catalog()
        if method == "GET" and path == "/api/ai/selected":
            return 200, self.get_selected()
        if method == "GET" and path == "/api/ai/models":
            result = self.get_models(provider_id or "")
            return (200 if result.get("ok") else 400), result
        if method == "POST" and path == "/api/ai/select":
            result = self.post_select(payload or {})
            return (200 if result.get("ok") else 400), result
        if method == "POST" and path == "/api/ai/test":
            result = self.post_connection_test()
            return (200 if result.get("ok") else 503), result
        return 404, {"ok": False, "error": "not found"}
