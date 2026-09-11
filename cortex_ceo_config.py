"""Safe construction of the optional AI advisory layer for Cortex CEO."""

from __future__ import annotations

import os
from typing import Any, Optional

from cortex_ai_control import load_selection
from cortex_ai_factory import build_runtime
from cortex_ai_runtime import AISelection


def ai_advisory_from_env() -> tuple[Optional[Any], Optional[AISelection], bool]:
    """Build the selected provider adapter from governed persisted configuration.

    The default remains disabled so Cortex stays deterministic when no AI service
    is configured. Credentials are resolved only by the server-side runtime.
    Legacy environment configuration remains supported as a compatibility path.
    """
    enabled = os.getenv("TJ_CORTEX_AI_AUGMENT", "false").strip().lower() in {"1", "true", "yes", "on"}

    persisted = load_selection()
    if persisted is not None:
        bundle = build_runtime(selection_path="cortex_ai_selection.json")
        if bundle is None:
            return None, persisted.to_runtime(), False
        return bundle.runtime, bundle.selection, enabled

    provider_id = os.getenv("TJ_CORTEX_AI_PROVIDER", "local_ollama").strip() or "local_ollama"
    model = os.getenv("TJ_CORTEX_AI_MODEL", "local-model").strip() or "local-model"
    try:
        selection = AISelection(provider_id, model)
    except (TypeError, ValueError):
        return None, None, False
    return None, selection, False
