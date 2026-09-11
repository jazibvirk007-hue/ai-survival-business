"""Cortex Retention Engine for evidence-based repeat revenue opportunities.

This module only reasons from observed customer/order metrics. It does not
invent retention, churn, revenue, or customer behavior and does not send
messages itself; communication remains governed by Cortex Guard.
"""

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Dict, List


@dataclass(frozen=True)
class RetentionOpportunity:
    name: str
    segment: str
    offer: str
    expected_revenue: float
    expected_cost: float
    probability: float = 1.0
    effort_hours: float = 1.0
    risk: float = 0.0
    requires_approval: bool = True

    def __post_init__(self) -> None:
        for field in ("name", "segment", "offer"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be non-empty")
        values = (self.expected_revenue, self.expected_cost, self.probability, self.effort_hours, self.risk)
        if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not isfinite(float(v)) for v in values):
            raise ValueError("retention values must be finite numbers")
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

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CortexRetention:
    """Calculate observed retention metrics and rank repeat-revenue ideas."""

    @staticmethod
    def customer_metrics(customers: int, repeat_customers: int, repeat_orders: int = 0) -> Dict[str, float]:
        for name, value in (("customers", customers), ("repeat_customers", repeat_customers), ("repeat_orders", repeat_orders)):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if repeat_customers > customers:
            raise ValueError("repeat_customers cannot exceed customers")
        return {
            "customers": float(customers),
            "repeat_customers": float(repeat_customers),
            "repeat_orders": float(repeat_orders),
            "repeat_customer_rate": repeat_customers / customers if customers else 0.0,
        }

    @staticmethod
    def rank(opportunities: List[RetentionOpportunity]) -> List[Dict[str, Any]]:
        if not isinstance(opportunities, list) or any(not isinstance(item, RetentionOpportunity) for item in opportunities):
            raise TypeError("opportunities must be a list of RetentionOpportunity objects")
        ranked: List[Dict[str, Any]] = []
        for item in opportunities:
            expected_profit = (item.expected_revenue - item.expected_cost) * item.probability
            risk_adjusted_profit = expected_profit * (1.0 - item.risk)
            score = risk_adjusted_profit / item.effort_hours
            row = item.to_dict()
            row.update({"expected_profit": expected_profit, "risk_adjusted_profit": risk_adjusted_profit, "profit_per_effort_hour": score})
            ranked.append(row)
        return sorted(ranked, key=lambda row: row["profit_per_effort_hour"], reverse=True)

    @staticmethod
    def next_actions(ranked: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        if not isinstance(ranked, list):
            raise TypeError("ranked must be a list")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
            raise ValueError("limit must be 1..50")
        actions: List[Dict[str, Any]] = []
        for item in ranked[:limit]:
            actions.append({
                "action": "execute_retention_opportunity" if item.get("requires_approval", True) else "prepare_retention_opportunity",
                "name": item["name"],
                "segment": item["segment"],
                "offer": item["offer"],
                "requires_approval": bool(item.get("requires_approval", True)),
                "reason": "ranked by risk-adjusted expected profit per effort hour",
            })
        return actions

    @staticmethod
    def status() -> Dict[str, Any]:
        return {
            "engine": "Cortex Retention Engine",
            "version": "1.0",
            "metrics": ["repeat_customer_rate", "repeat_orders"],
            "external_actions": "approval_gated",
            "data_policy": "observed_metrics_only",
            "spam": "prohibited",
        }
