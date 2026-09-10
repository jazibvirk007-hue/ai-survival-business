"""Bounded V8 CEO orchestration with explicit governance."""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from ai_ceo import AICEO, ACTIONS
from cortex_guard import CortexGuard


class CEOLoop:
    """Run bounded decision cycles and route governed actions through Guard."""

    def __init__(self, minimum_cash: float = 0.0, max_actions_per_cycle: int = 1, guard=None):
        self.ceo = AICEO(minimum_cash=minimum_cash, max_actions_per_cycle=max_actions_per_cycle)
        self.guard = guard if guard is not None else CortexGuard()
        if not isinstance(self.guard, CortexGuard):
            raise TypeError("guard must be a CortexGuard")
        self.handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self.outcomes: List[Dict[str, Any]] = []

    def register_handler(self, action: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        if action not in ACTIONS:
            raise ValueError(f"unsupported CEO action: {action}")
        if not callable(handler):
            raise TypeError("handler must be callable")
        self.handlers[action] = handler

    def cycle(self, state: Dict[str, Any], execute: bool = False, approval_id: Optional[str] = None) -> Dict[str, Any]:
        """Observe, decide, and optionally execute one safe handler.

        Approval-required decisions create a Guard request. Execution of such a
        decision requires the matching, unexpired approval id and consumes it
        before the handler runs, preventing approval replay.
        """
        if not isinstance(state, dict):
            raise TypeError("state must be a dictionary")

        decision = self.ceo.decide(state)
        result: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": decision.to_dict(),
            "executed": False,
            "approval_id": None,
            "outcome": None,
        }

        if decision.requires_approval:
            if not execute:
                request = self.guard.request(decision.action, decision.reason, decision.priority)
                result["approval_id"] = request["id"]
                result["outcome"] = "approval_required"
            elif not approval_id:
                result["outcome"] = "approval_required"
            else:
                try:
                    approval = self.guard.consume(approval_id, decision.action)
                    result["approval_id"] = approval["id"]
                    handler = self.handlers.get(decision.action)
                    if handler is None:
                        result["outcome"] = "handler_not_registered"
                    else:
                        try:
                            result["outcome"] = handler(dict(state))
                            result["executed"] = True
                        except Exception as error:
                            result["outcome"] = f"handler_failed: {type(error).__name__}: {error}"
                except (KeyError, ValueError) as error:
                    result["outcome"] = f"approval_denied: {error}"
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
            "version": "8.1",
            "cycles": len(self.outcomes),
            "registered_handlers": sorted(self.handlers),
            "execution_default": False,
            "external_irreversible_actions": "approval_required",
            "guard": self.guard.status(),
        }
