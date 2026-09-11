import os
import tempfile
import unittest
from unittest.mock import patch

from cortex_autonomous_growth_loop import AutonomousGrowthLoop
from cortex_v9_specialists import CortexV9Specialists, build_v9_loop


class CortexV9SpecialistsTests(unittest.TestCase):
    def test_build_registers_every_ceo_action(self):
        loop = build_v9_loop()
        self.assertEqual(
            set(loop.status()["registered_actions"]),
            {
                "research_market",
                "create_product",
                "find_prospects",
                "qualify_prospects",
                "draft_outreach",
                "follow_up",
                "review_financials",
                "improve_offer",
                "rest_and_observe",
            },
        )

    def test_research_adapter_uses_real_market_engine(self):
        specialists = CortexV9Specialists()
        fake_results = [{"opportunity": "ai automation", "score": 82.5}]
        with patch("cortex_v9_specialists.MarketResearch.research_opportunities", return_value=fake_results):
            result = specialists._research({"opportunity": "ai automation"})
        self.assertTrue(result["success"])
        self.assertEqual(result["results"], fake_results)
        self.assertTrue(result["state_patch"]["market_researched"])

    def test_product_adapter_creates_observed_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            old = os.getcwd()
            os.chdir(temp_dir)
            try:
                result = CortexV9Specialists._create_product({
                    "opportunity": "ai automation",
                    "research_results": [{"opportunity": "ai automation", "score": 80}],
                    "products_available": 0,
                })
            finally:
                os.chdir(old)
        self.assertTrue(result["success"])
        self.assertTrue(result["artifact_path"].endswith(".json"))
        self.assertEqual(result["state_patch"]["products_available"], 1)
        self.assertEqual(result["product"]["product_name"], "Small Business AI Automation Starter")

    def test_prospect_and_qualification_adapters_never_invent_records(self):
        specialists = CortexV9Specialists()
        missing = specialists._find_prospects({})
        self.assertFalse(missing["success"])
        self.assertEqual(missing["state_patch"]["qualified_prospects"], 0)

        records = [{
            "name": "Example Business",
            "source": "authorized_test_source",
            "problem_signal": "needs automation",
            "fit_score": 90,
            "intent_score": 85,
            "contactability": 70,
        }]
        found = specialists._find_prospects({"prospects": records})
        self.assertTrue(found["success"])
        self.assertEqual(found["count"], 1)
        qualified = specialists._qualify_prospects({"prospect_records": records})
        self.assertEqual(qualified["count"], 1)

    def test_outreach_is_preparation_only(self):
        specialists = CortexV9Specialists()
        result = specialists._draft_outreach({
            "qualified_records": [{"name": "Example Business", "category": "software"}],
            "latest_product": {"product_name": "Automation Starter"},
        })
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["drafts"][0]["status"], "draft")

        follow_up = specialists._follow_up(result["state_patch"])
        self.assertTrue(follow_up["success"])
        self.assertFalse(follow_up["sent"])
        self.assertFalse(follow_up["customer_response_observed"])

    def test_financial_adapter_uses_verified_observations(self):
        result = CortexV9Specialists._review_financials({
            "verified_revenue": 100,
            "verified_variable_cost": 20,
            "verified_customers": 2,
            "verified_acquisition_spend": 10,
            "verified_repeat_orders": 1,
        })
        self.assertTrue(result["success"])
        self.assertAlmostEqual(result["economics"]["gross_margin"], 0.8)
        self.assertTrue(result["recommendations"])

    def test_external_outreach_stays_guarded_by_loop(self):
        loop = build_v9_loop()
        state = {
            "market_researched": True,
            "products_available": 1,
            "qualified_prospects": 1,
            "outreach_drafts": 1,
            "approved_outreach": 1,
            "pending_orders": 0,
        }
        decision = loop.cycle(state, execute=False)
        self.assertEqual(decision["decision"]["action"], "follow_up")
        self.assertEqual(decision["outcome"], "approval_required")
        self.assertIsNotNone(decision["approval_id"])


if __name__ == "__main__":
    unittest.main()
