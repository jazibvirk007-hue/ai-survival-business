"""Safe construction of the optional AI advisory layer for Cortex CEO."""

from __future__ import annotations

import os
from typing import Any, Optional

from cortex_ai_catalog import get_provider
from cortex_ai_runtime import AISelection, CortexAIRuntime


def ai_advisory_from_env() -> tuple[Optional[Any], Optional[AISelection], bool]:
    """Build the selected provider adapter from server-side configuration.

    The default is disabled so Cortex remains deterministic when no AI service is
    configured. Provider IDs and model names are configuration, never credentials.
    """
    enabled = os.getenv("TJ_CORTEX_AI_AUGMENT", "false").strip().lower() in {"1", "true", "yes", "on"}
    provider_id = os.getenv("TJ_CORTEX_AI_PROVIDER", "local_ollama").strip() or "local_ollama"
    model = os.getenv("TJ_CORTEX_AI_MODEL", "local-model").strip() or "local-model"
    preset = get_provider(provider_id)
    if preset.protocol == "openai_compatible" and preset.provider_id == "custom_openai":
        base_url = os.getenv("TJ_CORTEX_AI_BASE_URL", "").strip()
        if not base_url:
            return None, AISelection(provider_id, model), False
        preset = type(preset)(preset.provider_id, preset.name, preset.family, base_url, preset.auth_env, preset.protocol, preset.docs_url, preset.supports_model_listing)
    selection = AISelection(provider_id, model)
    return CortexAIRuntime(), selection, enabled
