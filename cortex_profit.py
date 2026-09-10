"""Profit intelligence for TJ Cortex.

This module converts observed business metrics into conservative economics and
rankings. It never invents revenue, customers, costs, or conversion data.
"""

from dataclasses import dataclass, asdict
from math import isfinite
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class Opportunity:
    name: str
    expected_revenue: float
    expected_cost: float
    probability: float = 1.0
    effort_hours: float = 1.0
    risk: float = 0.0

    def __post_init__(self):
        values = (self.expected_revenue, self.expected_cost, self.probability, self.effort_hours, self.risk)
        if any(not isinstance(v, (int, float)) or not isfinite(float(v)) for v in values):
            raise ValueError("opportunity values must be finite numbers")
        if self.expected_revenue < 0 or self.expected_cost < 0:
            raise ValueError("revenue and cost cannot be negative")
        if not 0 <= self.probability <= 1:
            raise ValueError("probability must be between 0 and 1")
        if self.effort_hours <= 0:
            raise ValueError("effort_hours must be positive")
        if not 0 <= self.risk <= 1:
            raise ValueError("risk must be between 0 and 1")


class CortexProfit:
    """Conservative decision-support engine for profitable growth."""

    @staticmethod
    def _num(value: Any, name: str, minimum: Optional[float] = None) -> float:
        if not isinstance(value, (int, float)) or not isfinite(float(value)):
            raise ValueError(f"{name} must be a finite number")
        result = float(value)
        if minimum is not None and result < minimum:
            raise ValueError(f"{name} must be >= {minimum}")
        return result

    def unit_economics(self, revenue: float, variable_cost: float, customers: int,
                       acquisition_spend: float = 0.0, repeat_orders: int = 0,
                       gross_margin_target: float = 0.70) -> Dict[str, float]:
        revenue = self._num(revenue, "revenue", 0)
        variable_cost = self._num(variable_cost, "variable_cost", 0)
        acquisition_spend = self._num(acquisition_spend, "acquisition_spend", 0)
        if not isinstance(customers, int) or customers < 0:
            raise ValueError("customers must be a non-negative integer")
        if not isinstance(repeat_orders, int) or repeat_orders < 0:
            raise ValueError("repeat_orders must be a non-negative integer")
        target = self._num(gross_margin_target, "gross_margin_target", 0)
        if target >= 1:
            raise ValueError("gross_margin_target must be below 1")
        gross_profit = revenue - variable_cost
        margin = gross_profit / revenue if revenue else 0.0
        cac = acquisition_spend / customers if customers else None
        average_order_value = revenue / (customers + repeat_orders) if (customers + repeat_orders) else 0.0
        break_even_revenue = variable_cost / (1.0 - target) if target < 1 else None
        return {
            "revenue": revenue,
            "variable_cost": variable_cost,
            "gross_profit": gross_profit,
            "gross_margin": margin,
            "cac": cac,
            "average_order_value": average_order_value,
            "break_even_revenue_at_target_margin": break_even_revenue,
        }

    @staticmethod
    def ltv(average_order_value: float, purchase_frequency: float, gross_margin: float) -> float:
        aov = CortexProfit._num(average_order_value, "average_order_value", 0)
        frequency = CortexProfit._num(purchase_frequency, "purchase_frequency", 0)
        margin = CortexProfit._num(gross_margin, "gross_margin", 0)
        if margin > 1:
            raise ValueError("gross_margin cannot exceed 1")
        return aov * frequency * margin

    @staticmethod
    def runway_months(cash: float, monthly_fixed_cost: float, monthly_variable_burn: float = 0.0) -> Optional[float]:
        cash = CortexProfit._num(cash, "cash", 0)
        burn = CortexProfit._num(monthly_fixed_cost, "monthly_fixed_cost", 0) + CortexProfit._num(monthly_variable_burn, "monthly_variable_burn", 0)
        return None if burn == 0 else cash / burn

    @staticmethod
    def rank_opportunities(opportunities: Iterable[Opportunity]) -> List[Dict[str, Any]]:
        items = list(opportunities)
        if any(not isinstance(item, Opportunity) for item in items):
            raise TypeError("all opportunities must be Opportunity objects")
        ranked = []
        for item in items:
            expected_profit = (item.expected_revenue - item.expected_cost) * item.probability
            risk_adjusted_profit = expected_profit * (1.0 - item.risk)
            score = risk_adjusted_profit / item.effort_hours
            row = asdict(item)
            row.update({"expected_profit": expected_profit, "risk_adjusted_profit": risk_adjusted_profit, "profit_per_effort_hour": score})
            ranked.append(row)
        return sorted(ranked, key=lambda row: row["profit_per_effort_hour"], reverse=True)

    @staticmethod
    def detect_anomalies(current: Dict[str, float], baseline: Dict[str, float], threshold: float = 0.30) -> List[Dict[str, Any]]:
        if not isinstance(current, dict) or not isinstance(baseline, dict):
            raise TypeError("current and baseline must be dictionaries")
        threshold = CortexProfit._num(threshold, "threshold", 0)
        if threshold >= 1:
            raise ValueError("threshold must be below 1")
        anomalies = []
        for key, old in baseline.items():
            if key not in current:
                continue
            old_value = CortexProfit._num(old, f"baseline[{key}]")
            new_value = CortexProfit._num(current[key], f"current[{key}]")
            if old_value == 0:
                if new_value != 0:
                    anomalies.append({"metric": key, "baseline": old_value, "current": new_value, "change_ratio": None})
                continue
            ratio = (new_value - old_value) / abs(old_value)
            if abs(ratio) >= threshold:
                anomalies.append({"metric": key, "baseline": old_value, "current": new_value, "change_ratio": ratio})
        return anomalies

    def recommend(self, economics: Dict[str, Any]) -> List[str]:
        """Return conservative optimization priorities from supplied evidence."""
        if not isinstance(economics, dict):
            raise TypeError("economics must be a dictionary")
        recommendations = []
        margin = economics.get("gross_margin")
        cac = economics.get("cac")
        ltv = economics.get("ltv")
        runway = economics.get("runway_months")
        if isinstance(margin, (int, float)) and margin < 0.50:
            recommendations.append("improve gross margin before scaling acquisition")
        if isinstance(cac, (int, float)) and isinstance(ltv, (int, float)) and cac > 0 and ltv > 0 and ltv / cac < 3:
            recommendations.append("improve LTV or reduce CAC before increasing paid acquisition")
        if isinstance(runway, (int, float)) and runway < 3:
            recommendations.append("prioritize cash preservation and fast-payback offers")
        if not recommendations:
            recommendations.append("prioritize the highest risk-adjusted profit per unit of effort")
        return recommendations
