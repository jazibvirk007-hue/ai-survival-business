"""Unified bounded Cortex runtime.

Observe -> Decide -> Guard -> Execute -> Verify -> Learn -> Repeat.
The runtime composes revenue, growth, specialist registry, and bounded agent
factory systems without creating a second payment or authorization authority.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional
import uuid

from cortex_agent_factory import CortexAgentFactory, HiredAgent
from cortex_autonomous_growth_loop import AutonomousGrowthLoop
from cortex_revenue_loop import CortexRevenueLoop
from cortex_specialist_registry import CortexSpecialistRegistry


class CortexAutonomousRuntime:
    """Run one evidence-backed, bounded business transition per cycle."""

    VERSION = "20.0"
    MAX_TRANSITIONS_PER_CYCLE = 1

    def __init__(
        self,
        *,
        growth: Optional[AutonomousGrowthLoop] = None,
        revenue: Optional[CortexRevenueLoop] = None,
        specialists: Optional[CortexSpecialistRegistry] = None,
        agent_factory: Optional[CortexAgentFactory] = None,
    ) -> None:
        self.growth = growth if growth is not None else AutonomousGrowthLoop()
        self.revenue = revenue if revenue is not None else CortexRevenueLoop(guard=self.growth.guard)
        self.specialists = specialists if specialists is not None else CortexSpecialistRegistry()
        self.agent_factory = agent_factory if agent_factory is not None else CortexAgentFactory(self.specialists)
        if not isinstance(self.growth, AutonomousGrowthLoop):
            raise TypeError("growth must be AutonomousGrowthLoop")
        if not isinstance(self.revenue, CortexRevenueLoop):
            raise TypeError("revenue must be CortexRevenueLoop")
        if not isinstance(self.specialists, CortexSpecialistRegistry):
            raise TypeError("specialists must be CortexSpecialistRegistry")
        if not isinstance(self.agent_factory, CortexAgentFactory):
            raise TypeError("agent_factory must be CortexAgentFactory")
        self.history: list[Dict[str, Any]] = []

    def register(self, action: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        """Register one CEO action through the single specialist authority."""
        self.specialists.register(action, handler)
        self.growth.register(action, handler)

    def hire_agent(
        self,
        *,
        name: str,
        action: str,
        purpose: str,
        reason: str,
        handler: Callable[[Dict[str, Any]], Any],
        observed_workload: int = 1,
    ) -> HiredAgent:
        """Hire a new bounded specialist only when observed workload justifies it."""
        if not self.agent_factory.should_hire(action, observed_workload):
            raise ValueError("agent hiring is not justified or action is already staffed")
        hired = self.agent_factory.hire(
            name=name,
            action=action,
            purpose=purpose,
            reason=reason,
            handler=handler,
        )
        self.growth.register(action, handler)
        return hired

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
        base["specialist_registry"] = self.specialists.status()
        base["agent_factory"] = self.agent_factory.status()
        return base

    def cycle(
        self,
        state: Optional[Dict[str, Any]] = None,
        *,
        execute: bool = False,
        approval_id: Optional[str] = None,
        handler: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ) -> Dict[str, Any]:
        """Run exactly one governed growth transition."""
        observed = self.observe(state)
        cycle_id = "V20-" + uuid.uuid4().hex[:12].upper()
        decision = self.growth.ceo.decide(observed)
        if handler is not None:
            self.register(decision.action, handler)
        elif execute and decision.action in self.specialists.actions():
            self.growth.register(decision.action, self.specialists.get(decision.action))
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
            "specialist_registry": self.specialists.status(),
            "agent_factory": self.agent_factory.status(),
            "last_cycle_at": self.history[-1].get("timestamp") if self.history else None,
            "runtime_started_at": datetime.now(timezone.utc).isoformat(),
        }
