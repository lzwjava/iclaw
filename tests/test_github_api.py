import unittest
from unittest.mock import MagicMock, patch

from mini_copilot import github_api

class TestGithubApi(unittest.TestCase):
    @patch("mini_copilot.github_api.requests.get")
    def test_get_copilot_token_success(self, mock_get):
        mock_get.return_value = MagicMock(ok=True, json=lambda: {"token": "t"})
        self.assertEqual(github_api.get_copilot_token("gt"), "t")

    @patch("mini_copilot.github_api.requests.get")
    def test_get_copilot_token_failure(self, mock_get):
        mock_get.return_value = MagicMock(ok=False, status_code=401)
        with self.assertRaises(RuntimeError):
            github_api.get_copilot_token("it")

    @patch("mini_copilot.github_api.requests.get")
    def test_get_models(self, mock_get):
        mock_get.return_value = MagicMock(ok=True, json=lambda: {"data": [{"id": "m"}]})
        self.assertEqual(github_api.get_models("t")[0]["id"], "m")

    @patch("mini_copilot.github_api.requests.post")
    def test_chat(self, mock_post):
        mock_post.return_value = MagicMock(ok=True, json=lambda: {"choices": [{"message": {"content": "h"}}]})
        self.assertEqual(github_api.chat([], "t")["content"], "h")

if __name__ == "__main__":
    unittest.main()
