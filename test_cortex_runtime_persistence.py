import os
import tempfile
import unittest

from cortex_runtime_persistence import load_runtime_state, save_runtime_state


class RuntimePersistenceTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "runtime.json")
            state = {"state": {"opportunity": "automation"}, "history": [{"action": "research_market"}]}
            save_runtime_state(state, path)
            self.assertEqual(load_runtime_state(path), state)

    def test_missing_state_is_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(load_runtime_state(os.path.join(d, "missing.json")), {})

    def test_corrupt_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "runtime.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("not-json")
            with self.assertRaises(ValueError):
                load_runtime_state(path)

    def test_history_is_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                save_runtime_state({"history": [{}] * 201}, os.path.join(d, "runtime.json"))


if __name__ == "__main__":
    unittest.main()
