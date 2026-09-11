"""V9 Autonomous Growth Loop for TJ Cortex.

This is the orchestration backbone that connects the existing Cortex engines into
one bounded feedback loop:

observe -> CEO decision -> specialist handoff -> observed outcome -> learning.

A cycle performs at most one registered stage. External/customer-facing actions
remain guarded by the stage handler and Cortex Guard; this module never invents
customers, revenue, conversions, or successful outcomes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import uuid

from ai_ceo import AICEO
from cortex_communication import record_message
from cortex_guard import CortexGuard
from cortex_learning import CortexLearning
from cortex_memory import CortexMemory


STAGE_BY_ACTION = {
    "research_market": "Intelligence",
    "create_product": "Product",
    "find_prospects": "Growth",
    "qualify_prospects": "Growth",
    "draft_outreach": "Communications",
    "follow_up": "Communications",
    "review_financials": "Finance",
    "improve_offer": "Product",
    "rest_and_observe": "Memory",
}

EXTERNAL_ACTIONS = {"draft_outreach", "follow_up"}
MAX_HISTORY = 200


class AutonomousGrowthLoop:
    """Coordinate one governed V9 growth cycle at a time."""

    def __init__(
        self,
        *,
        minimum_cash: float = 0.0,
        max_actions_per_cycle: int = 1,
        guard: Optional[CortexGuard] = None,
        learning: Optional[CortexLearning] = None,
        communication_path: str = "cortex_communications.json",
    ) -> None:
        self.ceo = AICEO(minimum_cash=minimum_cash, max_actions_per_cycle=max_actions_per_cycle)
        self.guard = guard if guard is not None else CortexGuard()
        if not isinstance(self.guard, CortexGuard):
            raise TypeError("guard must be a CortexGuard")
        self.learning = learning if learning is not None else CortexLearning(CortexMemory())
        if not isinstance(self.learning, CortexLearning):
            raise TypeError("learning must be CortexLearning")
        self.communication_path = communication_path
        self.handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self.history: List[Dict[str, Any]] = []

    def register(self, action: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        """Register one specialist stage handler.

        Handlers receive a shallow copy of the observed state and must return an
        observed result. They should not bypass Guard or create fake outcomes.
        """
        if action not in STAGE_BY_ACTION:
            raise ValueError(f"unsupported growth action: {action}")
        if not callable(handler):
            raise TypeError("handler must be callable")
        self.handlers[action] = handler

    def _emit(self, sender: str, recipient: str, message_type: str, summary: str, correlation_id: str, *, status: str = "sent", metadata: Optional[Dict[str, Any]] = None) -> None:
        try:
            record_message(sender, recipient, message_type, summary, status=status, correlation_id=correlation_id, metadata=metadata, path=self.communication_path)
        except Exception:
            # Visualization/observability cannot break the business loop.
            pass

    @staticmethod
    def _success(result: Any) -> bool:
        if isinstance(result, dict) and "success" in result:
            return bool(result["success"])
        return result is not None

    def cycle(self, state: Dict[str, Any], *, execute: bool = False, approval_id: Optional[str] = None) -> Dict[str, Any]:
        """Run one bounded autonomous cycle.

        With execute=False (default), the loop produces a decision and a
        specialist handoff plan but performs no handler action. With execute=True,
        only a registered handler is called. External actions additionally require
        a matching, unexpired Guard approval.
        """
        if not isinstance(state, dict):
            raise TypeError("state must be a dictionary")

        cycle_id = "V9-" + uuid.uuid4().hex[:12].upper()
        decision = self.ceo.decide(state)
        action = decision.action
        stage = STAGE_BY_ACTION[action]
        result: Dict[str, Any] = {
            "cycle_id": cycle_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": decision.to_dict(),
            "stage": stage,
            "executed": False,
            "outcome": "decision_only",
            "approval_id": None,
        }

        try:
            self.learning.record_decision(action, decision.reason, int(decision.priority), decision.requires_approval)
        except Exception:
            pass
        self._emit("Cortex CEO", stage, "handoff", f"CEO selected {action} and handed work to {stage}", cycle_id, metadata={"priority": decision.priority})

        handler = self.handlers.get(action)
        if not execute:
            if action in EXTERNAL_ACTIONS or decision.requires_approval:
                request = self.guard.request(action, decision.reason, int(decision.priority))
                result["approval_id"] = request["id"]
                result["outcome"] = "approval_required"
                self._emit(stage, "Cortex Guard", "approval_request", f"{stage} requires approval before {action}", cycle_id, status="waiting", metadata={"approval_id": request["id"]})
            return self._finish(result)

        if handler is None:
            result["outcome"] = "handler_not_registered"
            self._emit("Cortex CEO", stage, "execution", f"No registered handler for {action}", cycle_id, status="failed")
            return self._finish(result)

        if action in EXTERNAL_ACTIONS or decision.requires_approval:
            if not approval_id:
                result["outcome"] = "approval_required"
                self._emit(stage, "Cortex Guard", "execution", f"Execution blocked: approval required for {action}", cycle_id, status="blocked")
                return self._finish(result)
            try:
                approval = self.guard.consume(approval_id, action)
                result["approval_id"] = approval["id"]
            except (KeyError, ValueError) as error:
                result["outcome"] = f"approval_denied: {error}"
                self._emit("Cortex Guard", stage, "approval", f"Approval denied for {action}", cycle_id, status="denied")
                return self._finish(result)

        try:
            self._emit(stage, STAGE_BY_ACTION.get(action, "Cortex CEO"), "execution", f"Executing {action}", cycle_id, status="started")
            outcome = handler(dict(state))
            result["outcome"] = outcome
            result["executed"] = True
            self._emit(stage, "Cortex CEO", "outcome", f"{stage} completed {action}", cycle_id, status="completed")
            try:
                self.learning.record_outcome(action, str(outcome), self._success(outcome))
            except Exception:
                pass
        except Exception as error:
            result["outcome"] = f"handler_failed: {type(error).__name__}: {error}"
            self._emit(stage, "Cortex CEO", "outcome", f"{stage} failed {action}: {type(error).__name__}", cycle_id, status="failed")
            try:
                self.learning.record_outcome(action, type(error).__name__, False)
            except Exception:
                pass

        return self._finish(result)

    def _finish(self, result: Dict[str, Any]) -> Dict[str, Any]:
        self.history.append(dict(result))
        if len(self.history) > MAX_HISTORY:
            self.history = self.history[-MAX_HISTORY:]
        return result

    def status(self) -> Dict[str, Any]:
        return {
            "engine": "Cortex V9 Autonomous Growth Loop",
            "version": "9.0",
            "cycles": len(self.history),
            "registered_actions": sorted(self.handlers),
            "pipeline": [
                "Research",
                "Opportunity",
                "Product",
                "Prospect",
                "Content/Outreach",
                "Customer",
                "Sale",
                "Delivery",
                "Profit",
                "Learning",
            ],
            "execution_policy": "one_bounded_stage_per_cycle",
            "external_actions": "Cortex Guard approval required",
            "revenue_policy": "verified_observations_only",
            "communication_stream": "live_event_bus",
        }
