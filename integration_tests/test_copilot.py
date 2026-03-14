import unittest
import os
import requests
from iclaw import github_api

class TestCopilotIntegration(unittest.TestCase):
    def setUp(self):
        self.github_token = os.environ.get("GITHUB_TOKEN_INTEGRATION")
        if not self.github_token:
            self.skipTest("GITHUB_TOKEN_INTEGRATION environment variable not set")

    def test_copilot_token_and_models(self):
        # Step 1: Exchange GitHub token for Copilot token
        try:
            copilot_token = github_api.get_copilot_token(self.github_token)
            self.assertTrue(len(copilot_token) > 0, "Copilot token should not be empty")
            print("\n✅ Successfully obtained Copilot token.")
        except Exception as e:
            self.fail(f"Failed to get Copilot token: {e}")

        # Step 2: Fetch available models
        try:
            models = github_api.get_models(copilot_token)
            self.assertIsInstance(models, list, "Models should be a list")
            self.assertTrue(len(models) > 0, "Should find at least one model")
            model_ids = [m['id'] for m in models]
            print(f"✅ Found {len(models)} models. Available: {', '.join(model_ids[:5])}...")
        except Exception as e:
            self.fail(f"Failed to fetch models: {e}")

    def test_copilot_chat(self):
        copilot_token = github_api.get_copilot_token(self.github_token)
        messages = [{"role": "user", "content": "Say 'hello world' and nothing else."}]
        
        try:
            response = github_api.chat(messages, copilot_token, model="gpt-4o")
            content = response.get("content", "").lower()
            self.assertIn("hello world", content)
            print(f"✅ Copilot Chat responded correctly: {content}")
        except Exception as e:
            self.fail(f"Chat integration failed: {e}")

if __name__ == "__main__":
    unittest.main()
