"""Bounded V8 CEO orchestration primitives.

The loop observes supplied business state, asks the AI CEO for one bounded
next action, and optionally executes only explicitly registered safe handlers.
It does not send outreach, move money, verify payments, or deliver orders by
itself. Those operations remain behind their existing approval/trust gates.
"""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from ai_ceo import AICEO, Decision, ACTIONS


class CEOLoop:
    """Run one bounded decision cycle against an observed state."""

    def __init__(self, minimum_cash: float = 0.0, max_actions_per_cycle: int = 1):
        self.ceo = AICEO(minimum_cash=minimum_cash, max_actions_per_cycle=max_actions_per_cycle)
        self.handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self.outcomes: List[Dict[str, Any]] = []

    def register_handler(self, action: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        if action not in ACTIONS:
            raise ValueError(f"unsupported CEO action: {action}")
        if not callable(handler):
            raise TypeError("handler must be callable")
        self.handlers[action] = handler

    def cycle(self, state: Dict[str, Any], execute: bool = False) -> Dict[str, Any]:
        """Observe, decide, and optionally run one registered safe handler."""
        if not isinstance(state, dict):
            raise TypeError("state must be a dictionary")

        decision = self.ceo.decide(state)
        result: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": decision.to_dict(),
            "executed": False,
            "outcome": None,
        }

        if execute and decision.requires_approval:
            result["outcome"] = "approval_required"
        elif execute:
            handler = self.handlers.get(decision.action)
            if handler is None:
                result["outcome"] = "handler_not_registered"
            else:
                try:
                    result["outcome"] = handler(dict(state))
                    result["executed"] = True
                except Exception as error:
                    result["outcome"] = f"handler_failed: {type(error).__name__}: {error}"
        else:
            result["outcome"] = "decision_only"

        self.outcomes.append(result)
        return result

    def status(self) -> Dict[str, Any]:
        return {
            "engine": "AI CEO loop",
            "version": "8.0",
            "cycles": len(self.outcomes),
            "registered_handlers": sorted(self.handlers),
            "execution_default": False,
            "external_irreversible_actions": "approval_required",
        }
