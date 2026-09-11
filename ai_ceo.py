"""AI CEO decision engine.

V8 turns observed business state into a bounded, explainable next action.
V8.2 adds conservative profit-aware prioritization using observed economics.
It never fabricates revenue and never performs irreversible external actions.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List


ACTIONS = (
    "research_market",
    "create_product",
    "find_prospects",
    "qualify_prospects",
    "draft_outreach",
    "follow_up",
    "review_financials",
    "improve_offer",
    "rest_and_observe",
)


@dataclass(frozen=True)
class Decision:
    action: str
    priority: float
    reason: str
    expected_outcome: str
    requires_approval: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AICEO:
    """Choose the safest highest-value next business action from observed state."""

    def __init__(self, minimum_cash: float = 0.0, max_actions_per_cycle: int = 1):
        if minimum_cash < 0:
            raise ValueError("minimum_cash cannot be negative")
        if max_actions_per_cycle < 1:
            raise ValueError("max_actions_per_cycle must be positive")
        self.minimum_cash = float(minimum_cash)
        self.max_actions_per_cycle = int(max_actions_per_cycle)
        self.history: List[Dict[str, Any]] = []

    @staticmethod
    def _number(state: Dict[str, Any], key: str, default: float = 0.0) -> float:
        try:
            value = float(state.get(key, default))
            return value if value == value and value not in (float("inf"), float("-inf")) else default
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _profit_adjustment(action: str, state: Dict[str, Any]) -> float:
        """Apply small bounded adjustments from observed unit economics.

        The adjustment is intentionally capped so economics can influence, but
        never completely override, operational safety priorities.
        """
        adjustment = 0.0
        margin = state.get("gross_margin")
        cac = state.get("cac")
        ltv = state.get("ltv")
        runway = state.get("runway_months")
        if isinstance(margin, (int, float)) and margin == margin:
            if margin < 0.50 and action == "improve_offer":
                adjustment += 12
            elif margin >= 0.70 and action in {"find_prospects", "follow_up"}:
                adjustment += 4
        if isinstance(cac, (int, float)) and isinstance(ltv, (int, float)) and cac > 0 and ltv > 0:
            ratio = ltv / cac
            if ratio < 3 and action in {"improve_offer", "review_financials"}:
                adjustment += 10
            elif ratio >= 5 and action in {"find_prospects", "follow_up"}:
                adjustment += 5
        if isinstance(runway, (int, float)) and runway >= 0 and runway < 3:
            if action == "review_financials":
                adjustment += 12
            elif action in {"follow_up", "find_prospects"}:
                adjustment += 4
            elif action == "create_product":
                adjustment -= 4
        return max(-10.0, min(15.0, adjustment))

    def evaluate(self, state: Dict[str, Any]) -> List[Decision]:
        """Return ranked candidate decisions without executing any action."""
        if not isinstance(state, dict):
            raise TypeError("state must be a dictionary")

        revenue = max(0.0, self._number(state, "verified_revenue"))
        cash = max(0.0, self._number(state, "cash", revenue))
        prospects = max(0, int(self._number(state, "qualified_prospects")))
        drafts = max(0, int(self._number(state, "outreach_drafts")))
        approved = max(0, int(self._number(state, "approved_outreach")))
        pending = max(0, int(self._number(state, "pending_orders")))
        products = max(0, int(self._number(state, "products_available")))
        market_age_default = 0 if state.get("market_researched", False) else 9999
        market_age = max(0.0, self._number(state, "market_research_age_hours", market_age_default))
        recent_failure = bool(state.get("recent_action_failed", False))

        candidates: List[Decision] = []
        if recent_failure:
            candidates.append(Decision("rest_and_observe", 96, "The previous cycle failed; pause before repeating the same action.", "Preserve resources and gather a clean next observation."))
        if market_age > 24 or not state.get("market_researched", False):
            candidates.append(Decision("research_market", 90, "Market evidence is missing or stale.", "Refresh opportunity signals before spending effort on acquisition."))
        if state.get("market_researched", False) and products == 0:
            candidates.append(Decision("create_product", 88, "A market opportunity exists but no sellable offer is ready.", "Create one concrete offer before prospecting."))
        if products > 0 and prospects == 0:
            candidates.append(Decision("find_prospects", 84, "A product exists but there are no qualified prospects.", "Build a real prospect pool without inventing customers."))
        if prospects > 0 and drafts == 0:
            candidates.append(Decision("qualify_prospects", 80, "Qualified prospect data exists but outreach preparation is empty.", "Prepare the strongest real prospects for relevant outreach."))
        if drafts > 0 and approved == 0:
            candidates.append(Decision("draft_outreach", 76, "Qualified prospects exist without an approved outreach draft.", "Prepare personalized outreach for human/provider-approved sending."))
        if pending > 0:
            candidates.append(Decision("review_financials", 75, "There are pending orders that must remain payment-gated.", "Check verified payment state without counting unpaid orders as revenue."))
        if approved > 0 and pending == 0:
            candidates.append(Decision("follow_up", 72, "Approved outreach exists but no resulting order is pending.", "Follow up through permitted channels and seek a real customer response.", True))
        if revenue > 0 and not candidates:
            candidates.append(Decision("improve_offer", 55, "Revenue exists and no urgent operational blocker is visible.", "Use observed results to improve conversion or customer value."))
        if cash < self.minimum_cash:
            candidates.append(Decision("review_financials", 99, "Observed cash is below the configured survival floor.", "Protect liquidity and avoid discretionary spending until the floor is restored."))
        if not candidates:
            candidates.append(Decision("research_market", 50, "There is insufficient evidence for a higher-confidence action.", "Collect market evidence before making a consequential decision."))

        adjusted: List[Decision] = []
        for decision in candidates:
            bonus = self._profit_adjustment(decision.action, state)
            if bonus:
                reason = f"{decision.reason} Profit intelligence adjustment: {bonus:+.0f} based only on observed economics."
                decision = Decision(decision.action, max(0.0, min(100.0, decision.priority + bonus)), reason, decision.expected_outcome, decision.requires_approval)
            adjusted.append(decision)
        return sorted(adjusted, key=lambda item: item.priority, reverse=True)[: max(1, self.max_actions_per_cycle)]

    def decide(self, state: Dict[str, Any]) -> Decision:
        decision = self.evaluate(state)[0]
        self.history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": decision.to_dict(),
            "verified_revenue": max(0.0, self._number(state, "verified_revenue")),
            "cash": max(0.0, self._number(state, "cash", 0.0)),
        })
        return decision

    def status(self) -> Dict[str, Any]:
        return {
            "engine": "AI CEO",
            "version": "8.2",
            "decisions_recorded": len(self.history),
            "max_actions_per_cycle": self.max_actions_per_cycle,
            "minimum_cash": self.minimum_cash,
            "profit_intelligence": "bounded_observed_economics",
            "execution_policy": "decision_only; irreversible actions require explicit approval",
        }
