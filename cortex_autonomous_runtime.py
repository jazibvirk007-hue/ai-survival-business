"""Unified bounded Cortex runtime.

Observe -> Decide -> Guard -> Execute -> Verify -> Learn -> Repeat.
The runtime composes the existing revenue and growth systems instead of
creating a second payment, customer, or authorization authority.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional
import uuid

from cortex_autonomous_growth_loop import AutonomousGrowthLoop
from cortex_revenue_loop import CortexRevenueLoop


class CortexAutonomousRuntime:
    """Run one evidence-backed, bounded business transition per cycle."""

    VERSION = "19.0"
    MAX_TRANSITIONS_PER_CYCLE = 1

    def __init__(
        self,
        *,
        growth: Optional[AutonomousGrowthLoop] = None,
        revenue: Optional[CortexRevenueLoop] = None,
    ) -> None:
        self.growth = growth if growth is not None else AutonomousGrowthLoop()
        self.revenue = revenue if revenue is not None else CortexRevenueLoop(guard=self.growth.guard)
        if not isinstance(self.growth, AutonomousGrowthLoop):
            raise TypeError("growth must be AutonomousGrowthLoop")
        if not isinstance(self.revenue, CortexRevenueLoop):
            raise TypeError("revenue must be CortexRevenueLoop")
        self.history: list[Dict[str, Any]] = []

    def observe(self, state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Merge caller observations with authoritative revenue observations."""
        base = dict(state or {})
        revenue = self.revenue.observe()
        base["revenue_snapshot"] = dict(revenue)
        base["verified_revenue"] = revenue["verified_revenue"]
        base["pending_orders"] = revenue["pending_orders"]
        base["paid_orders"] = revenue["paid_orders"]
        base["pending_payments"] = revenue["pending_payments"]
        base["delivered_orders"] = revenue["delivered_orders"]
        base["truth_policy"] = "verified_observations_only"
        return base

    def cycle(
        self,
        state: Optional[Dict[str, Any]] = None,
        *,
        execute: bool = False,
        approval_id: Optional[str] = None,
        handler: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ) -> Dict[str, Any]:
        """Run exactly one governed growth transition.

        A supplied handler is registered only for the CEO-selected action, and
        external/irreversible actions remain subject to the existing Guard.
        """
        observed = self.observe(state)
        cycle_id = "V19-" + uuid.uuid4().hex[:12].upper()
        if handler is not None:
            decision = self.growth.ceo.decide(observed)
            self.growth.register(decision.action, handler)
        result = self.growth.cycle(observed, execute=execute, approval_id=approval_id)
        result["runtime_cycle_id"] = cycle_id
        result["observed_revenue"] = observed["verified_revenue"]
        result["revenue_snapshot"] = observed["revenue_snapshot"]
        result["verification"] = "provider_authoritative"
        result["transition_budget"] = self.MAX_TRANSITIONS_PER_CYCLE
        self.history.append(dict(result))
        self.history = self.history[-200:]
        return result

    def status(self) -> Dict[str, Any]:
        return {
            "engine": "Cortex Autonomous Runtime",
            "version": self.VERSION,
            "cycles": len(self.history),
            "control_loop": ["observe", "decide", "guard", "execute", "verify", "learn", "repeat"],
            "max_transitions_per_cycle": self.MAX_TRANSITIONS_PER_CYCLE,
            "payment_authority": "independently_confirmed_provider_event",
            "revenue_policy": "verified_observations_only",
            "execution_policy": "decision_only_by_default; governed execution when explicitly enabled",
            "last_cycle_at": self.history[-1].get("timestamp") if self.history else None,
            "runtime_started_at": datetime.now(timezone.utc).isoformat(),
        }
