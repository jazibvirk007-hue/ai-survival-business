"""Governed AI provider/model selection for Cortex Link.

Selections are stored without credentials. API keys remain server-side environment
variables and are never accepted from or returned to the UI.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

from cortex_ai_catalog import get_provider, providers
from cortex_ai_runtime import AISelection, CortexAIRuntime

DEFAULT_PATH = Path("cortex_ai_selection.json")
MAX_MODEL_LENGTH = 200


@dataclass(frozen=True)
class AIControlSelection:
    provider_id: str
    model: str

    def to_runtime(self) -> AISelection:
        return AISelection(self.provider_id, self.model)


def _validate(provider_id: str, model: str) -> AIControlSelection:
    if not isinstance(provider_id, str) or not provider_id.strip():
        raise ValueError("provider_id is required")
    if not isinstance(model, str) or not model.strip() or len(model) > MAX_MODEL_LENGTH:
        raise ValueError("model is required and must be <= 200 characters")
    get_provider(provider_id)
    return AIControlSelection(provider_id.strip(), model.strip())


def load_selection(path: os.PathLike[str] | str = DEFAULT_PATH) -> Optional[AIControlSelection]:
    target = Path(path)
    if not target.exists():
        return None
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        return _validate(data.get("provider_id", ""), data.get("model", ""))
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return None


def save_selection(selection: AIControlSelection, path: os.PathLike[str] | str = DEFAULT_PATH) -> None:
    selection = _validate(selection.provider_id, selection.model)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(asdict(selection), handle, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, target)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def safe_provider_catalog() -> list[dict[str, Any]]:
    """Return only browser-safe provider metadata; omit credential env names."""
    return [
        {
            key: value
            for key, value in item.items()
            if key != "auth_env"
        }
        for item in providers()
    ]


def safe_selection_status(runtime: CortexAIRuntime, path: os.PathLike[str] | str = DEFAULT_PATH) -> dict[str, Any]:
    selection = load_selection(path)
    if selection is None:
        return {"selected": False, "provider_id": "", "model": "", "configured": False}
    status = runtime.status(selection.to_runtime())
    status.pop("credential_env", None)
    status["selected"] = True
    return status


def discover_models(runtime: CortexAIRuntime, provider_id: str) -> list[str]:
    """Discover live models; credentials are resolved only by the server runtime."""
    get_provider(provider_id)
    return runtime.discover_models(provider_id)
