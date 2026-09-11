"""V9 specialist adapters for TJ Cortex.

Binds the V9 orchestration backbone to the real specialist engines already in
this repository. Preparation is separated from customer-facing execution;
outbound actions remain Cortex Guard controlled.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from cortex_acquisition_pipeline import CortexAcquisitionPipeline
from cortex_agent_factory import CortexAgentFactory
from cortex_autonomous_growth_loop import AutonomousGrowthLoop
from cortex_growth import CortexGrowth
from cortex_profit import CortexProfit
from cortex_prospecting import CortexProspecting
from cortex_retention import CortexRetention
from market_research import MarketResearch
from outreach import OutreachGenerator
from product_factory import ProductFactory

_MAX_ITEMS = 20
_MAX_TEXT = 2000


def _text(value: Any, limit: int = _MAX_TEXT) -> str:
    return str(value)[:limit] if value is not None else ""


def _list(value: Any, limit: int = _MAX_ITEMS) -> List[Any]:
    return list(value)[:limit] if isinstance(value, (list, tuple)) else []


def _first_nonempty(*values: Any) -> Optional[str]:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


class CortexV9Specialists:
    """Adapter facade around the repository's existing specialist engines."""

    def __init__(self) -> None:
        self.research = MarketResearch()
        self.prospecting = CortexProspecting()
        self.acquisition = CortexAcquisitionPipeline(prospecting=self.prospecting)
        self.growth = CortexGrowth()
        self.profit = CortexProfit()
        self.retention = CortexRetention()
        self.outreach = OutreachGenerator()
        self.agent_factory = CortexAgentFactory()

    def _research(self, state: Dict[str, Any]) -> Dict[str, Any]:
        opportunities = _list(state.get("opportunities"), 10)
        opportunity = _first_nonempty(state.get("opportunity"))
        if not opportunities and opportunity:
            opportunities = [opportunity]
        if not opportunities:
            opportunities = [
                "small business marketing", "social media content", "ai automation",
                "presentation design", "product description", "youtube script",
                "short video script",
            ]
        opportunities = [x for x in opportunities if isinstance(x, str) and x.strip()]
        if not opportunities:
            return {"success": False, "reason": "no valid opportunities supplied"}
        results = self.research.research_opportunities(opportunities[:10])
        ranked = self.research.rank(results) if results else []
        return {
            "success": bool(results),
            "observed": "market_research",
            "results": results[:10],
            "ranked_opportunities": ranked[:10],
            "state_patch": {
                "market_researched": bool(results),
                "market_research_age_hours": 0,
                "research_results": results[:10],
                "opportunities": [r.get("opportunity") for r in ranked[:10] if isinstance(r, dict)],
            },
        }

    @staticmethod
    def _create_product(state: Dict[str, Any]) -> Dict[str, Any]:
        research = _list(state.get("research_results"))
        opportunity = _first_nonempty(
            state.get("opportunity"),
            research[0].get("opportunity") if research and isinstance(research[0], dict) else None,
        )
        if not opportunity:
            return {"success": False, "reason": "no researched opportunity available"}
        factory = ProductFactory()
        product = factory.build_product(opportunity, research[0] if research else {})
        path = factory.save_product(product)
        return {
            "success": True,
            "observed": "product_created",
            "product": product,
            "artifact_path": _text(path, 500),
            "state_patch": {
                "products_available": max(0, int(state.get("products_available", 0) or 0)) + 1,
                "latest_product": product,
                "latest_product_path": _text(path, 500),
            },
        }

    def _find_prospects(self, state: Dict[str, Any]) -> Dict[str, Any]:
        records = state.get("prospects")
        if records is None:
            return {
                "success": False,
                "observed": "prospect_source_missing",
                "reason": "No authorized prospect records were supplied; no customers are invented.",
                "state_patch": {"qualified_prospects": 0},
            }
        try:
            plan = self.acquisition.plan(_list(records, 50), limit=20)
        except (TypeError, ValueError):
            return {"success": False, "observed": "prospect_discovery_rejected",
                    "reason": "prospect records failed acquisition-policy validation",
                    "state_patch": {"qualified_prospects": 0}}
        candidates = plan.get("candidates", [])
        reviewed = plan.get("reviewed", [])
        return {
            "success": True,
            "observed": "prospect_discovery",
            "count": len(reviewed),
            "eligible_count": len(candidates),
            "ranked_prospects": reviewed[:20],
            "acquisition_queue": candidates[:20],
            "state_patch": {
                "prospect_records": reviewed[:20],
                "qualified_prospects": len(candidates),
                "qualified_records": candidates[:20],
            },
        }

    @staticmethod
    def _qualify_prospects(state: Dict[str, Any]) -> Dict[str, Any]:
        records = state.get("qualified_records", state.get("prospect_records", state.get("prospects")))
        if records is None:
            return {"success": False, "reason": "no prospect records supplied"}
        try:
            prospects = CortexProspecting.discover(_list(records, 50))
            ranked = CortexProspecting.rank(prospects)
        except (TypeError, ValueError):
            return {"success": False, "reason": "prospect records failed qualification validation"}
        qualified = [r for r in ranked if r.get("priority_score", 0) >= 60][:20]
        return {
            "success": True, "observed": "prospect_qualification",
            "qualified": qualified, "count": len(qualified),
            "state_patch": {"qualified_prospects": len(qualified), "qualified_records": qualified},
        }

    def _draft_outreach(self, state: Dict[str, Any]) -> Dict[str, Any]:
        prospects = _list(state.get("qualified_records", state.get("prospect_records")))
        product = state.get("latest_product")
        if not isinstance(product, dict):
            return {"success": False, "reason": "no generated product available"}
        drafts = []
        for prospect in prospects:
            if isinstance(prospect, dict) and prospect.get("name"):
                drafts.append(self.outreach.generate(prospect, product))
        if not drafts:
            return {"success": False, "reason": "no qualified prospects available for draft preparation"}
        return {"success": True, "observed": "outreach_drafts_prepared", "drafts": drafts[:20],
                "count": len(drafts[:20]),
                "state_patch": {"outreach_drafts": len(drafts[:20]), "draft_records": drafts[:20]}}

    @staticmethod
    def _follow_up(state: Dict[str, Any]) -> Dict[str, Any]:
        drafts = _list(state.get("draft_records"), 20)
        return {"success": bool(drafts), "observed": "follow_up_preparation",
                "prepared_count": len(drafts), "sent": False,
                "customer_response_observed": False,
                "reason": "Follow-up is prepared only; sending remains provider/Guard controlled."}

    @staticmethod
    def _review_financials(state: Dict[str, Any]) -> Dict[str, Any]:
        economics = state.get("economics")
        if isinstance(economics, dict):
            return {"success": True, "observed": "financial_review", "economics": economics,
                    "recommendations": CortexProfit().recommend(economics)}
        revenue = max(0.0, float(state.get("verified_revenue", 0.0) or 0.0))
        variable_cost = max(0.0, float(state.get("verified_variable_cost", 0.0) or 0.0))
        customers = max(0, int(state.get("verified_customers", 0) or 0))
        spend = max(0.0, float(state.get("verified_acquisition_spend", 0.0) or 0.0))
        repeat_orders = max(0, int(state.get("verified_repeat_orders", 0) or 0))
        observed = CortexProfit().unit_economics(revenue, variable_cost, customers, spend, repeat_orders)
        return {"success": True, "observed": "financial_review", "economics": observed,
                "recommendations": CortexProfit().recommend(observed)}

    @staticmethod
    def _improve_offer(state: Dict[str, Any]) -> Dict[str, Any]:
        product = state.get("latest_product")
        if not isinstance(product, dict):
            return {"success": False, "reason": "no product observed to improve"}
        return {"success": True, "observed": "offer_improvement_plan",
                "current_product": _text(product.get("product_name"), 300),
                "observed_gross_margin": state.get("gross_margin"),
                "recommendations": [
                    "review price against verified delivery cost",
                    "clarify the highest-value deliverable",
                    "test a smaller starter offer before adding acquisition spend",
                ]}

    @staticmethod
    def _rest(state: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "observed": "rest_and_observe",
                "reason": "preserve resources and collect the next clean observation"}

    def register_all(self, loop: AutonomousGrowthLoop) -> AutonomousGrowthLoop:
        if not isinstance(loop, AutonomousGrowthLoop):
            raise TypeError("loop must be AutonomousGrowthLoop")
        for action, handler in {
            "research_market": self._research,
            "create_product": self._create_product,
            "find_prospects": self._find_prospects,
            "qualify_prospects": self._qualify_prospects,
            "draft_outreach": self._draft_outreach,
            "follow_up": self._follow_up,
            "review_financials": self._review_financials,
            "improve_offer": self._improve_offer,
            "rest_and_observe": self._rest,
        }.items():
            loop.register(action, handler)
        return loop


def build_v9_loop(**kwargs: Any) -> AutonomousGrowthLoop:
    return CortexV9Specialists().register_all(AutonomousGrowthLoop(**kwargs))
