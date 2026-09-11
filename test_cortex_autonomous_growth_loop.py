        self.assertFalse(result["executed"])
        self.assertIn("handler_failed", result["outcome"])
        context = self.learning.context(10)
        self.assertTrue(any(item["kind"] == "outcome" and item["metadata"].get("success") is False for item in context))

    def test_status_exposes_v9_pipeline_without_fake_metrics(self):
        status = self.loop.status()
        self.assertEqual(status["version"], "9.2")
        self.assertEqual(status["execution_policy"], "one_bounded_stage_per_cycle")
        self.assertEqual(status["revenue_policy"], "verified_observations_only")
        self.assertIn("Profit", status["pipeline"])


if __name__ == "__main__":
    unittest.main()