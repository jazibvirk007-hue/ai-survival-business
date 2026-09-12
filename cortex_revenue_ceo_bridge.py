"""Bridge verified revenue observations into the bounded AI CEO loop.

The bridge is deliberately thin: it translates factual revenue-loop state into
CEO-observable state and registers only governed handlers. It never fabricates
payments, customers, revenue, or provider confirmations.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from ai_ceo import AICEO
from cortex_guard import CortexGuard
from cortex_revenue_loop import CortexRevenueLoop


class CortexRevenueCEOBridge:
    """Connect revenue lifecycle observations to bounded CEO decisions."""

    def __init__(self, revenue_loop: Optional[CortexRevenueLoop] = None,
                 ceo: Optional[AICEO] = None,
                 guard: Optional[CortexGuard] = None) -> None:
        self.revenue_loop = revenue_loop or CortexRevenueLoop(guard=guard)
        self.ceo = ceo or AICEO(max_actions_per_cycle=1)
        self.guard = guard or self.revenue_loop.guard
        self.handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

    def observe(self, base_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Merge factual revenue state into an optional CEO observation."""
        state = dict(base_state or {})
        revenue = self.revenue_loop.observe()
        state.update(revenue)
        state.setdefault("products_available", 0)
        state.setdefault("qualified_prospects", 0)
        state.setdefault("outreach_drafts", 0)
        state.setdefault("approved_outreach", 0)
        state.setdefault("market_researched", True)
        return state

    def decide(self, base_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return the CEO decision using current verified revenue observations."""
        state = self.observe(base_state)
        return self.ceo.decide(state).to_dict()

    def register_handler(self, action: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        if not isinstance(action, str) or not action.strip():
            raise ValueError("action is required")
        if not callable(handler):
            raise TypeError("handler must be callable")
        self.handlers[action] = handler

    def cycle(self, base_state: Optional[Dict[str, Any]] = None, execute: bool = False,
              approval_id: Optional[str] = None) -> Dict[str, Any]:
        """Run one bounded revenue-aware CEO transition.

        Unknown actions remain decision-only. Approval is required for handlers
        registered as governed actions; the bridge never performs payment
        verification itself.
        """
        state = self.observe(base_state)
        decision = self.ceo.decide(state)
        result: Dict[str, Any] = {
            "decision": decision.to_dict(),
            "observed_revenue_state": self.revenue_loop.observe(),
            "executed": False,
            "outcome": "decision_only",
            "approval_id": None,
        }
        if not execute:
            return result

        handler = self.handlers.get(decision.action)
        if handler is None:
            result["outcome"] = "handler_not_registered"
            return result

        if decision.requires_approval:
            if not approval_id:
                request = self.guard.request(decision.action, decision.reason, int(decision.priority))
                result["approval_id"] = request["id"]
                result["outcome"] = "approval_required"
                return result
            approval = self.guard.consume(approval_id, decision.action)
            result["approval_id"] = approval["id"]

        result["outcome"] = handler(dict(state))
        result["executed"] = True
        return result

    def status(self) -> Dict[str, Any]:
        return {
            "engine": "Cortex Revenue CEO Bridge",
            "version": "13.1",
            "revenue_truth": "verified_observations_only",
            "payment_authority": self.revenue_loop.status()["payment_authority"],
            "registered_handlers": sorted(self.handlers),
            "execution": "bounded_one_transition",
            "guard": self.guard.status(),
        }
