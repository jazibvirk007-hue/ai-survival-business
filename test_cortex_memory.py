import json
import os
import tempfile
import unittest
from unittest.mock import patch

from cortex_memory import CortexMemory


class MemoryTests(unittest.TestCase):
    def test_remember_and_recent_are_persistent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "memory.json")
            memory = CortexMemory(path=path, max_entries=3)
            entry = memory.remember("decision", "Research the market", {"priority": 80, "api_key": "must-not-store"})
            self.assertEqual(entry["kind"], "decision")
            self.assertNotIn("api_key", entry["metadata"])
            restored = CortexMemory(path=path, max_entries=3)
            self.assertEqual(restored.recent(1)[0]["content"], "Research the market")

    def test_memory_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = CortexMemory(os.path.join(directory, "memory.json"), max_entries=2)
            memory.remember("a", "one")
            memory.remember("b", "two")
            memory.remember("c", "three")
            self.assertEqual([item["kind"] for item in memory.recent(10)], ["b", "c"])

    def test_corrupt_store_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "memory.json")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("not-json")
            with self.assertRaises(json.JSONDecodeError):
                CortexMemory(path).recent()

    def test_secret_like_metadata_keys_are_filtered(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = CortexMemory(os.path.join(directory, "memory.json"))
            entry = memory.remember("note", "safe", {"api_key": "x", "token": "y", "customer": "demo"})
            self.assertEqual(entry["metadata"], {"customer": "demo"})

    def test_invalid_input_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = CortexMemory(os.path.join(directory, "memory.json"))
            with self.assertRaises(ValueError):
                memory.remember("", "content")
            with self.assertRaises(ValueError):
                memory.remember("kind", "")
            with self.assertRaises(TypeError):
                memory.remember("kind", "content", [])

    def test_atomic_save_uses_replace(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = CortexMemory(os.path.join(directory, "memory.json"))
            with patch("cortex_memory.os.replace", wraps=os.replace) as replace:
                memory.remember("test", "atomic")
            replace.assert_called_once()


if __name__ == "__main__":
    unittest.main()
