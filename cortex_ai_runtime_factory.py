"""Build the governed AI runtime from persisted Cortex Link configuration."""

from __future__ import annotations

from typing import Any

from cortex_ai_control import DEFAULT_PATH, load_selection, safe_selection_status
from cortex_ai_runtime import CortexAIRuntime


def build_configured_ai(*, selection_path: str = str(DEFAULT_PATH), timeout_seconds: float = 30.0) -> dict[str, Any]:
    """Return a safe runtime bundle; absence of configuration is normal."""
    runtime = CortexAIRuntime(timeout_seconds=timeout_seconds)
    selection = load_selection(selection_path)
    if selection is None:
        return {"runtime": runtime, "selection": None, "status": {"selected": False}}
    return {
        "runtime": runtime,
        "selection": selection.to_runtime(),
        "status": safe_selection_status(runtime, selection_path),
    }
