import json
import os
import tempfile
import unittest
from unittest.mock import patch

from cortex_autonomy_runtime import CortexAutonomyRuntime, PATCHABLE_FIELDS


class CortexAutonomyRuntimeTests(unittest.TestCase):
    def test_research_patch_advances_operational_state(self):
        runtime = CortexAutonomyRuntime({"opportunity": "ai automation"})
        fake = [{"opportunity": "ai automation", "score": 91}]
        with patch("cortex_v9_specialists.MarketResearch.research_opportunities", return_value=fake):
            result = runtime.step(execute=True)
        self.assertTrue(result["executed"])
        self.assertTrue(runtime.state["market_researched"])
        self.assertIn("research_results", result["applied_state_patch"])
        self.assertNotIn("verified_revenue", result["applied_state_patch"])

    def test_runtime_never_allows_financial_truth_to_be_patched(self):
        runtime = CortexAutonomyRuntime({"verified_revenue": 125, "cash": 50, "recent_action_failed": True})
        runtime.loop.register("rest_and_observe", lambda state: {
            "success": True,
            "state_patch": {
                "verified_revenue": 999999,
                "cash": 999999,
                "market_researched": True,
            },
        })
        result = runtime.step(execute=True)
        self.assertTrue(result["executed"])
        self.assertEqual(runtime.state["verified_revenue"], 125)
        self.assertEqual(runtime.state["cash"], 50)
        self.assertTrue(runtime.state["market_researched"])
        self.assertTrue(PATCHABLE_FIELDS.isdisjoint({"verified_revenue", "cash"}))

    def test_failed_handler_sets_failure_observation(self):
        runtime = CortexAutonomyRuntime({"recent_action_failed": True})
        runtime.loop.register("rest_and_observe", lambda state: (_ for _ in ()).throw(RuntimeError("boom")))
        result = runtime.step(execute=True)
        self.assertFalse(result["executed"])
        self.assertTrue(runtime.state["recent_action_failed"])
        self.assertIn("handler_failed", result["outcome"])

    def test_snapshot_exposes_real_runtime_state(self):
        runtime = CortexAutonomyRuntime({"market_researched": True, "verified_revenue": 10})
        snapshot = runtime.snapshot()
        self.assertEqual(snapshot["state"]["verified_revenue"], 10)
        self.assertEqual(snapshot["version"], "10.2")
        self.assertIn("research_market", snapshot["registered_actions"])
        self.assertTrue(snapshot["persistence"]["restart_safe"])

    def test_runtime_restores_state_and_history_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "runtime.json")
            first = CortexAutonomyRuntime(initial_state={"market_researched": True}, state_path=path)
            first.history.append({"cycle_id": "cycle-1", "action": "research_market", "executed": False})
            first._persist()

            second = CortexAutonomyRuntime(initial_state={"market_researched": False}, state_path=path)
            self.assertTrue(second.state["market_researched"])
            self.assertEqual(len(second.history), 1)
            self.assertEqual(second.persistence_status, "restored")

    def test_corrupt_persistence_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "runtime.json")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("{not-json")
            runtime = CortexAutonomyRuntime(initial_state={"market_researched": False}, state_path=path)
            self.assertEqual(runtime.persistence_status, "corrupt_state")
            self.assertFalse(runtime.state.get("market_researched", True))

    def test_persisted_shape_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "runtime.json")
            runtime = CortexAutonomyRuntime(initial_state={"market_researched": True}, state_path=path)
            runtime._persist()
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            self.assertEqual(set(data), {"state", "history"})


if __name__ == "__main__":
    unittest.main()
