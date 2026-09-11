            AICEO().decide([])
        with self.assertRaises(ValueError):
            AICEO(minimum_cash=-1)
        with self.assertRaises(ValueError):
            AICEO(max_actions_per_cycle=0)

    def test_decisions_are_explainable_and_bounded(self):
        ceo = AICEO(max_actions_per_cycle=1)
        decision = ceo.decide({"market_researched": True, "products_available": 1})
        self.assertTrue(decision.reason)
        self.assertTrue(decision.expected_outcome)
        self.assertEqual(ceo.status()["max_actions_per_cycle"], 1)
        self.assertEqual(ceo.status()["execution_policy"], "decision_only; model output cannot authorize actions; irreversible actions require explicit approval")


if __name__ == "__main__":
    unittest.main()