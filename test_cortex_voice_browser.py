import unittest


class BrowserVoiceContractTests(unittest.TestCase):
    def test_browser_voice_surface_contract(self):
        with open("cortex_voice_browser.js", "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn("window.SpeechRecognition", source)
        self.assertIn("/api/voice", source)
        self.assertIn('Content-Type', source)
        self.assertIn('CortexVoiceCEO', source)
        self.assertIn('MAX_TRANSCRIPT', source)


if __name__ == "__main__":
    unittest.main()
