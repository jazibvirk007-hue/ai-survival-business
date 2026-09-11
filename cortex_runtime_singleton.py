"""Shared Cortex runtime authority for dashboard and scheduler integration."""
from __future__ import annotations

from cortex_v95_orchestrator import CortexV95Orchestrator

_RUNTIME: CortexV95Orchestrator | None = None


def get_cortex_orchestrator() -> CortexV95Orchestrator:
    global _RUNTIME
    if _RUNTIME is None:
        _RUNTIME = CortexV95Orchestrator()
    return _RUNTIME


def reset_cortex_orchestrator() -> None:
    """Reset the process-local reference without deleting persisted state."""
    global _RUNTIME
    _RUNTIME = None
