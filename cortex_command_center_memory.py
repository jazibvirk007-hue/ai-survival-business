"""Browser-safe Deep Memory and strategy feedback surface."""

from __future__ import annotations

from typing import Any, Optional

from cortex_deep_memory import CortexDeepMemory
from cortex_memory import CortexMemory
from cortex_strategy_feedback import CortexStrategyFeedback


def build_memory_snapshot(memory: Optional[CortexMemory] = None) -> dict[str, Any]:
    """Expose bounded learning intelligence without execution authority."""
    deep = CortexDeepMemory(memory or CortexMemory())
    feedback = CortexStrategyFeedback(deep)
    return feedback.build()
