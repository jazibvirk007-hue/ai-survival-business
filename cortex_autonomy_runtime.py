"""Stateful V10 autonomy runtime with observed-learning strategy feedback."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from cortex_autonomous_growth_loop import AutonomousGrowthLoop
from cortex_deep_memory import CortexDeepMemory
from cortex_strategy_ceo import CortexStrategyCEO
from cortex_v9_specialists import build_v9_loop

PATCHABLE_FIELDS = frozenset({
    "market_researched", "market_research_age_hours", "research_results", "opportunities",
    "products_available", "latest_product", "latest_product_path", "prospect_records",
    "qualified_prospects", "qualified_records", "outreach_drafts", "draft_records",
    "economics", "recent_action_failed",
})
MAX_HISTORY = 200

class CortexAutonomyRuntime:
    """Persist bounded observations and use observed learning in CEO ranking."""
    def __init__(self, initial_state: Optional[Dict[str, Any]] = None, *, loop: Optional[AutonomousGrowthLoop] = None, max_history: int = MAX_HISTORY) -> None:
        if initial_state is not None and not isinstance(initial_state, dict): raise TypeError("initial_state must be a dictionary")
        if loop is not None and not isinstance(loop, AutonomousGrowthLoop): raise TypeError("loop must be AutonomousGrowthLoop")
        if not isinstance(max_history, int) or isinstance(max_history, bool) or not 1 <= max_history <= 1000: raise ValueError("max_history must be between 1 and 1000")
        self.loop = loop if loop is not None else build_v9_loop()
        self.loop.ceo = CortexStrategyCEO(self.loop.ceo)
        self.state: Dict[str, Any] = dict(initial_state or {})
        self.history: List[Dict[str, Any]] = []
        self.max_history = max_history
        self.deep_memory = CortexDeepMemory(self.loop.learning.memory)

    @staticmethod
    def _patch_from(result: Dict[str, Any]) -> Dict[str, Any]:
        outcome = result.get("outcome")
        if not isinstance(outcome, dict): return {}
        patch = outcome.get("state_patch")
        if not isinstance(patch, dict): return {}
        return {key: value for key, value in patch.items() if key in PATCHABLE_FIELDS}

    def _strategy_context(self) -> list[dict[str, Any]]:
        try: return self.deep_memory.context(10)
        except Exception: return []

    def step(self, *, execute: bool = False, approval_id: Optional[str] = None) -> Dict[str, Any]:
        before = dict(self.state)
        working_state = dict(self.state)
        strategy = self._strategy_context()
        working_state["memory_strategy"] = strategy
        result = self.loop.cycle(working_state, execute=execute, approval_id=approval_id)
        patch = self._patch_from(result) if result.get("executed") else {}
        if patch:
            self.state.update(patch)
            self.state["recent_action_failed"] = False
        elif result.get("executed") and isinstance(result.get("outcome"), dict) and result["outcome"].get("success") is False:
            self.state["recent_action_failed"] = True
        elif isinstance(result.get("outcome"), str) and result.get("outcome", "").startswith("handler_failed"):
            self.state["recent_action_failed"] = True
        result["memory_strategy"] = strategy
        self.history.append({"cycle_id": result.get("cycle_id"), "action": result.get("decision", {}).get("action"), "executed": bool(result.get("executed")), "outcome": result.get("outcome"), "applied_fields": sorted(patch)})
        if len(self.history) > self.max_history: self.history = self.history[-self.max_history:]
        result["applied_state_patch"] = patch
        result["state_changed"] = before != self.state
        return result

    def snapshot(self) -> Dict[str, Any]:
        return {
            "engine": "Cortex Autonomous Runtime",
            "version": "10.1",
            "state": dict(self.state),
            "history_count": len(self.history),
            "registered_actions": self.loop.status()["registered_actions"],
            "memory_strategy": self._strategy_context(),
            "learning_policy": "bounded observed outcomes influence ranking only",
            "truth_policy": "verified financial observations are immutable; memory is advisory only",
        }
