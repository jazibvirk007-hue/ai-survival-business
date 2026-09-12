"""Governed registry for Cortex specialist handlers.

The registry maps only known CEO actions to injected handlers. It does not
create external identities, authorize payments, or bypass Cortex Guard.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from ai_ceo import ACTIONS


class CortexSpecialistRegistry:
    VERSION = "15.0"

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

    def register(self, action: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        if action not in ACTIONS:
            raise ValueError(f"unsupported CEO action: {action}")
        if not callable(handler):
            raise TypeError("handler must be callable")
        self._handlers[action] = handler

    def get(self, action: str) -> Optional[Callable[[Dict[str, Any]], Any]]:
        return self._handlers.get(action)

    def actions(self) -> list[str]:
        return sorted(self._handlers)

    def dispatch(self, action: str, state: Dict[str, Any]) -> Any:
        handler = self.get(action)
        if handler is None:
            raise KeyError(f"no specialist registered for {action}")
        return handler(dict(state))

    def status(self) -> Dict[str, Any]:
        return {"version": self.VERSION, "registered_actions": self.actions(), "allowed_actions": list(ACTIONS), "authorization": "handlers cannot authorize actions"}
