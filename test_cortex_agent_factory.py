import unittest

from cortex_agent_factory import CortexAgentFactory, AgentProductSpec


class CortexAgentFactoryTests(unittest.TestCase):
    def make_spec(self):
        return AgentProductSpec(
            "Support Agent Pro",
            "customer_support",
            "Answer repetitive support questions",
            "small online stores",
            ["answer FAQs", "classify tickets", "escalate complex cases"],
            ["customer message", "FAQ knowledge base"],
            ["draft reply", "ticket category", "escalation flag"],
            ["webhook", "knowledge base"],
            49,
        )

    def test_customer_demand_creates_agent_spec(self):
        spec = CortexAgentFactory.from_customer_demand(
            "Automate support", "small stores", "customer_support",
            ["answer questions"], ["message"], ["reply"], ["webhook"], 29,
            "Store Support Agent",
        )
        self.assertEqual(spec.category, "customer_support")
        self.assertTrue(spec.requires_approval)

    def test_package_manifest_declares_artifacts(self):
        package = CortexAgentFactory.build_package(self.make_spec())
        self.assertEqual(package["product_type"], "ai_agent")
        self.assertIn("setup_guide.md", package["artifacts"])
        self.assertEqual(package["external_actions"], "approval_gated")

    def test_quality_gate_passes_valid_agent(self):
        result = CortexAgentFactory.quality_gate(self.make_spec())
        self.assertTrue(result["passed"])

    def test_invalid_category_rejected(self):
        with self.assertRaises(ValueError):
            AgentProductSpec("x", "unknown", "problem", "customer", ["a"], ["i"], ["o"], ["integration"], 10)

    def test_empty_capabilities_rejected(self):
        with self.assertRaises(ValueError):
            AgentProductSpec("x", "custom", "problem", "customer", [], ["i"], ["o"], ["integration"], 10)


if __name__ == "__main__":
    unittest.main()
