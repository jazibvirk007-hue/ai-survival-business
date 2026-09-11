"""Bounded V8 CEO orchestration with explicit governance and observability."""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from ai_ceo import AICEO, ACTIONS
from cortex_communication import record_message
from cortex_guard import CortexGuard


class CEOLoop:
    """Run bounded decision cycles and publish real agent communication events."""

    def __init__(self, minimum_cash: float = 0.0, max_actions_per_cycle: int = 1, guard=None, communication_path: str = "cortex_communications.json"):
        self.ceo = AICEO(minimum_cash=minimum_cash, max_actions_per_cycle=max_actions_per_cycle)
        self.guard = guard if guard is not None else CortexGuard()
        if not isinstance(self.guard, CortexGuard):
            raise TypeError("guard must be a CortexGuard")
        self.handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self.outcomes: List[Dict[str, Any]] = []
        self.communication_path = communication_path

    def register_handler(self, action: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        if action not in ACTIONS:
            raise ValueError(f"unsupported CEO action: {action}")
        if not callable(handler):
            raise TypeError("handler must be callable")
        self.handlers[action] = handler

    def _emit(self, recipient: str, message_type: str, summary: str, *, status: str = "sent", correlation_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        try:
            record_message("Cortex CEO", recipient, message_type, summary, status=status, correlation_id=correlation_id, metadata=metadata, path=self.communication_path)
        except Exception:
            # Observability must never make a business decision fail.
            pass

    def cycle(self, state: Dict[str, Any], execute: bool = False, approval_id: Optional[str] = None) -> Dict[str, Any]:
        """Observe, decide, and optionally execute one safe handler.

        Approval-required decisions create a Guard request. Execution of such a
        decision requires the matching, unexpired approval id. The approval is
        consumed only after a handler is confirmed to exist, so a configuration
        error cannot burn a valid human approval.
        """
        if not isinstance(state, dict):
            raise TypeError("state must be a dictionary")

        decision = self.ceo.decide(state)
        correlation_id = "CYCLE-" + str(len(self.outcomes) + 1)
        self._emit(
            decision.action,
            "decision",
            f"CEO selected {decision.action}: {decision.reason}",
            correlation_id=correlation_id,
            metadata={"priority": decision.priority, "requires_approval": decision.requires_approval},
        )
        result: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": decision.to_dict(),
            "executed": False,
            "approval_id": None,
            "outcome": None,
            "correlation_id": correlation_id,
        }

        if decision.requires_approval:
            if not execute:
                request = self.guard.request(decision.action, decision.reason, decision.priority)
                result["approval_id"] = request["id"]
                result["outcome"] = "approval_required"
                self._emit(decision.action, "approval_request", f"Approval requested before executing {decision.action}", status="waiting", correlation_id=correlation_id, metadata={"approval_id": request["id"]})
            elif not approval_id:
                result["outcome"] = "approval_required"
                self._emit(decision.action, "approval_request", f"Execution blocked: approval required for {decision.action}", status="blocked", correlation_id=correlation_id)
            else:
                handler = self.handlers.get(decision.action)
                if handler is None:
                    result["outcome"] = "handler_not_registered"
                    self._emit(decision.action, "execution", f"Execution blocked: no handler registered for {decision.action}", status="failed", correlation_id=correlation_id)
                else:
                    try:
                        approval = self.guard.consume(approval_id, decision.action)
                        result["approval_id"] = approval["id"]
                        try:
                            result["outcome"] = handler(dict(state))
                            result["executed"] = True
                            self._emit(decision.action, "execution", f"Executed approved action {decision.action}", status="completed", correlation_id=correlation_id)
                        except Exception as error:
                            result["outcome"] = f"handler_failed: {type(error).__name__}: {error}"
                            self._emit(decision.action, "execution", f"Handler failed for {decision.action}: {type(error).__name__}", status="failed", correlation_id=correlation_id)
                    except (KeyError, ValueError) as error:
                        result["outcome"] = f"approval_denied: {error}"
                        self._emit(decision.action, "approval", f"Approval denied for {decision.action}", status="denied", correlation_id=correlation_id)
        elif execute:
            handler = self.handlers.get(decision.action)
            if handler is None:
                result["outcome"] = "handler_not_registered"
                self._emit(decision.action, "execution", f"Execution blocked: no handler registered for {decision.action}", status="failed", correlation_id=correlation_id)
            else:
                try:
                    result["outcome"] = handler(dict(state))
                    result["executed"] = True
                    self._emit(decision.action, "execution", f"Executed action {decision.action}", status="completed", correlation_id=correlation_id)
                except Exception as error:
                    result["outcome"] = f"handler_failed: {type(error).__name__}: {error}"
                    self._emit(decision.action, "execution", f"Handler failed for {decision.action}: {type(error).__name__}", status="failed", correlation_id=correlation_id)
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
            "communication_stream": "enabled",
        }
