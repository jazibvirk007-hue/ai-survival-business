"""Profit-aware growth planning for TJ Cortex.

Growth recommendations are decision support only. The engine never sends
messages, buys ads, spends money, or claims conversions that were not observed.
External communication and paid acquisition should remain behind Cortex Guard.
"""

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Dict, Iterable, List, Optional

from cortex_profit import CortexProfit, Opportunity


@dataclass(frozen=True)
class GrowthOpportunity:
    name: str
    channel: str
    offer: str
    audience: str
    expected_revenue: float
    expected_cost: float
    probability: float = 1.0
    effort_hours: float = 1.0
    risk: float = 0.0
    requires_approval: bool = True

    def __post_init__(self) -> None:
        for field_name in ("name", "channel", "offer", "audience"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be non-empty")
        values = (self.expected_revenue, self.expected_cost, self.probability, self.effort_hours, self.risk)
        if any(not isinstance(v, (int, float)) or not isfinite(float(v)) for v in values):
            raise ValueError("growth opportunity values must be finite numbers")
        if self.expected_revenue < 0 or self.expected_cost < 0:
            raise ValueError("revenue and cost cannot be negative")
        if not 0 <= self.probability <= 1:
            raise ValueError("probability must be between 0 and 1")
        if self.effort_hours <= 0:
            raise ValueError("effort_hours must be positive")
        if not 0 <= self.risk <= 1:
            raise ValueError("risk must be between 0 and 1")
        if not isinstance(self.requires_approval, bool):
            raise ValueError("requires_approval must be boolean")


class CortexGrowth:
    """Rank acquisition ideas using observed economics and bounded assumptions."""

    @staticmethod
    def _count(value: Any, name: str) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
        return value

    @staticmethod
    def funnel_metrics(visits: int, leads: int, qualified: int, conversions: int, revenue: float = 0.0) -> Dict[str, Optional[float]]:
        visits = CortexGrowth._count(visits, "visits")
        leads = CortexGrowth._count(leads, "leads")
        qualified = CortexGrowth._count(qualified, "qualified")
        conversions = CortexGrowth._count(conversions, "conversions")
        if leads > visits or qualified > leads or conversions > qualified:
            raise ValueError("funnel counts must be non-increasing")
        if not isinstance(revenue, (int, float)) or not isfinite(float(revenue)) or revenue < 0:
            raise ValueError("revenue must be a non-negative finite number")
        return {
            "visits": visits,
            "leads": leads,
            "qualified": qualified,
            "conversions": conversions,
            "lead_rate": leads / visits if visits else None,
            "qualification_rate": qualified / leads if leads else None,
            "conversion_rate": conversions / qualified if qualified else None,
            "revenue_per_visit": revenue / visits if visits else None,
            "revenue_per_conversion": revenue / conversions if conversions else None,
        }

    @staticmethod
    def rank(opportunities: Iterable[GrowthOpportunity]) -> List[Dict[str, Any]]:
        items = list(opportunities)
        if any(not isinstance(item, GrowthOpportunity) for item in items):
            raise TypeError("all opportunities must be GrowthOpportunity objects")
        ranked = CortexProfit.rank_opportunities(
            Opportunity(
                name=item.name,
                expected_revenue=item.expected_revenue,
                expected_cost=item.expected_cost,
                probability=item.probability,
                effort_hours=item.effort_hours,
                risk=item.risk,
            )
            for item in items
        )
        by_name = {item.name: item for item in items}
        for row in ranked:
            source = by_name[row["name"]]
            row.update({"channel": source.channel, "offer": source.offer, "audience": source.audience, "requires_approval": source.requires_approval})
        return ranked

    @staticmethod
    def next_actions(ranked: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not isinstance(ranked, list):
            raise TypeError("ranked must be a list")
        actions = []
        for item in ranked[:10]:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                raise ValueError("ranked entries must be dictionaries with a name")
            actions.append({
                "action": "execute_growth_opportunity" if item.get("requires_approval", True) else "prepare_growth_opportunity",
                "opportunity": item["name"],
                "channel": item.get("channel"),
                "reason": "highest risk-adjusted profit per effort among supplied opportunities",
                "requires_approval": bool(item.get("requires_approval", True)),
            })
        return actions

    def status(self) -> Dict[str, Any]:
        return {"engine": "Cortex Growth Engine", "version": "1.0", "external_actions": "guarded"}
