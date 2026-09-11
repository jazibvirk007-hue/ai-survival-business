"""Safe construction of the currently selected Cortex AI runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cortex_ai_control import DEFAULT_PATH, load_selection
from cortex_ai_runtime import AISelection, CortexAIRuntime


@dataclass(frozen=True)
class AIRuntimeBundle:
    runtime: CortexAIRuntime
    selection: AISelection


def build_runtime(*, selection_path=DEFAULT_PATH, opener=None, timeout_seconds: float = 30.0) -> Optional[AIRuntimeBundle]:
    """Build the selected runtime, or return None when no governed selection exists."""
    selection = load_selection(selection_path)
    if selection is None:
        return None
    kwargs = {"timeout_seconds": timeout_seconds}
    if opener is not None:
        kwargs["opener"] = opener
    runtime = CortexAIRuntime(**kwargs)
    return AIRuntimeBundle(runtime=runtime, selection=selection.to_runtime())
