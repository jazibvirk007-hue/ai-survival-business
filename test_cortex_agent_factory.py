import json
import tempfile
import unittest
from pathlib import Path

from cortex_agent_factory import CortexAgentFactory, AgentProductSpec
from cortex_specialist_registry import CortexSpecialistRegistry


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

    def test_hire_request_is_bounded_and_audited(self):
        with tempfile.TemporaryDirectory() as tmp:
            factory = CortexAgentFactory(CortexSpecialistRegistry(), str(Path(tmp) / "workforce.json"))
            request = factory.propose_hire(
                action="research_market", workload=7,
                reason="Market research backlog", proposed_name="Research Specialist",
                purpose="Handle bounded research workload",
            )
            self.assertEqual(request.status, "proposed")
            payload = json.loads((Path(tmp) / "workforce.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["hire_requests"][0]["action"], "research_market")
            self.assertEqual(payload["hired_agents"], [])

    def test_hired_agent_metadata_survives_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "workforce.json")
            registry = CortexSpecialistRegistry()
            factory = CortexAgentFactory(registry, path)
            factory.hire(
                name="Research Specialist", action="research_market",
                purpose="Bounded research", reason="Observed workload",
                handler=lambda state: {"success": True},
            )
            restored = CortexAgentFactory(CortexSpecialistRegistry(), path)
            self.assertEqual(restored.status()["hired_agents"], 1)
            self.assertEqual(restored.roster()[0]["action"], "research_market")

    def test_invalid_persisted_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workforce.json"
            path.write_text("not-json", encoding="utf-8")
            factory = CortexAgentFactory(CortexSpecialistRegistry(), str(path))
            self.assertEqual(factory.status()["hired_agents"], 0)
            self.assertEqual(factory.status()["hire_requests"], 0)


if __name__ == "__main__":
    unittest.main()
