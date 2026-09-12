from __future__ import annotations

import unittest

from cortex_specialist_registry import CortexSpecialistRegistry


class TestCortexSpecialistRegistry(unittest.TestCase):
    def test_rejects_unknown_action(self) -> None:
        registry = CortexSpecialistRegistry()
        with self.assertRaises(ValueError):
            registry.register("send_money", lambda state: None)

    def test_dispatches_registered_action(self) -> None:
        registry = CortexSpecialistRegistry()
        registry.register("research_market", lambda state: {"success": True})
        self.assertEqual(registry.dispatch("research_market", {"x": 1})["success"], True)


if __name__ == "__main__":
    unittest.main()
