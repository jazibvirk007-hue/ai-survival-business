import tempfile
import unittest
from pathlib import Path

from cortex_local_health import build_local_health


class LocalHealthTests(unittest.TestCase):
    def test_repo_health_is_bounded_and_secret_free(self):
        result = build_local_health(Path(__file__).resolve().parent)
        self.assertIn(result["status"], {"READY", "DEGRADED"})
        self.assertFalse(result["secrets_checked"])
        self.assertNotIn("key", str(result).lower())

    def test_missing_asset_degrades(self):
        with tempfile.TemporaryDirectory() as directory:
            result = build_local_health(directory)
            self.assertEqual(result["status"], "DEGRADED")
            self.assertTrue(any(value == "MISSING" for value in result["assets"].values()))


if __name__ == "__main__":
    unittest.main()
