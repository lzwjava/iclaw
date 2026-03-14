import json
import unittest
from unittest.mock import MagicMock, patch

from mini_copilot import github_api, main, web_search, login


class TestMiniCopilot(unittest.TestCase):
    # --- Github API Tests ---
    @patch("mini_copilot.github_api.requests.get")
    def test_get_copilot_token_success(self, mock_get):
        mock_get.return_value = MagicMock(ok=True, json=lambda: {"token": "fake_token"})
        token = github_api.get_copilot_token("fake_github_token")
        self.assertEqual(token, "fake_token")

    @patch("mini_copilot.github_api.requests.get")
    def test_get_copilot_token_failure(self, mock_get):
        mock_get.return_value = MagicMock(ok=False, status_code=401, reason="Unauthorized")
        with self.assertRaises(RuntimeError):
            github_api.get_copilot_token("invalid_token")

    @patch("mini_copilot.github_api.requests.get")
    def test_get_models(self, mock_get):
        mock_get.return_value = MagicMock(ok=True, json=lambda: {"data": [{"id": "gpt-4"}]})
        models = github_api.get_models("fake_token")
        self.assertEqual(models[0]["id"], "gpt-4")

    @patch("mini_copilot.github_api.requests.post")
    def test_chat(self, mock_post):
        mock_post.return_value = MagicMock(ok=True, json=lambda: {"choices": [{"message": {"content": "Hello!"}}]})
        response = github_api.chat([], "token")
        self.assertEqual(response["content"], "Hello!")

    # --- Web Search Tests ---
    @patch("mini_copilot.web_search.requests.get")
    def test_search_ddg(self, mock_get):
        mock_get.return_value = MagicMock(ok=True, text='<html><div class="result__title"><a class="result__a" href="u">T</a></div></html>')
        results = web_search.search_ddg("q", num_results=1)
        self.assertEqual(results[0]["title"], "T")

    @patch("mini_copilot.web_search.requests.Session")
    def test_extract_text_from_url_various(self, mock_session):
        mock_s = MagicMock()
        mock_session.return_value = mock_s
        
        # Wikipedia
        mock_s.get.return_value = MagicMock(ok=True, status_code=200, text='<html><div id="firstHeading">WikiTitle</div></html>', apparent_encoding='utf-8')
        mock_s.get.return_value.apparent_encoding = 'utf-8' # Ensure encoding set
        self.assertIn("WikiTitle", web_search.extract_text_from_url("https://en.wikipedia.org/wiki/T"))
        
        # Github
        mock_s.get.return_value.text = '<html><article class="markdown-body">GitContent</article></html>'
        self.assertIn("GitContent", web_search.extract_text_from_url("https://github.com/u/r"))
        
        # Zhihu
        mock_s.get.return_value.text = '<html><div class="RichContent-inner">ZhihuContent</div></html>'
        self.assertIn("ZhihuContent", web_search.extract_text_from_url("https://zhihu.com/q/1"))

        # Fallback readability
        mock_s.get.return_value.text = '<html><body><main>MainContent</main></body></html>'
        self.assertIn("MainContent", web_search.extract_text_from_url("https://example.com"))

    def test_format_llm_output(self):
        output = web_search.format_llm_output([{"title": "T", "url": "U", "content": "C"}])
        self.assertIn("### Source 1", output)

    @patch("mini_copilot.web_search.search_ddg")
    @patch("mini_copilot.web_search.extract_text_from_url")
    def test_web_search_wrapper(self, mock_ext, mock_src):
        mock_src.return_value = [{"title": "T", "url": "U"}]
        mock_ext.return_value = "C"
        output = web_search.web_search("q", num_results=1)
        self.assertIn("Source 1", output)

    # --- Login Tests ---
    @patch("mini_copilot.login.requests.post")
    def test_login_flow(self, mock_post):
        # get_device_code
        mock_post.return_value = MagicMock(ok=True, json=lambda: {"device_code": "dc", "user_code": "uc", "verification_uri": "v"})
        res = login.get_device_code()
        self.assertEqual(res["device_code"], "dc")
        
        # poll_for_access_token (success)
        mock_post.side_effect = None
        mock_post.return_value = MagicMock(ok=True, json=lambda: {"access_token": "at"})
        with patch("mini_copilot.login.time.sleep"):
            token = login.poll_for_access_token("dc", 1)
            self.assertEqual(token, "at")

    # --- Main Tests ---
    @patch("mini_copilot.main.chat")
    @patch("mini_copilot.main.web_search")
    @patch("mini_copilot.main.get_copilot_token")
    @patch("mini_copilot.main.load_github_token")
    @patch("mini_copilot.main.input")
    def test_main_commands(self, mock_input, mock_load, mock_get_token, mock_search, mock_chat):
        mock_load.return_value = "gt"
        mock_get_token.return_value = "ct"
        # Test /help, /copy, /model, /search_provider, normal input, then exit
        mock_input.side_effect = ["/help", "/copy", "/model", "", "/search_provider", "1", "Ask something", ".exit"]
        mock_chat.side_effect = [{"role": "assistant", "content": "Reply"}]
        
        with patch("sys.stdout"), patch("mini_copilot.main.copy_to_clipboard"), \
             patch("mini_copilot.main.get_models", return_value=[{"id": "m1", "owned_by": "o1"}]), \
             patch("mini_copilot.main.time.monotonic", return_value=0):
            main.main()

    # --- Tool Call Handling ---
    @patch("mini_copilot.main.chat")
    @patch("mini_copilot.main.web_search")
    @patch("mini_copilot.main.get_copilot_token")
    @patch("mini_copilot.main.load_github_token")
    @patch("mini_copilot.main.input")
    def test_main_tool_calling(self, mock_input, mock_load, mock_get_token, mock_search, mock_chat):
        mock_load.return_value = "gt"
        mock_get_token.return_value = "ct"
        # First call hits a tool, second call returns content
        mock_chat.side_effect = [
            {"role": "assistant", "tool_calls": [{"id": "sid", "function": {"name": "web_search", "arguments": '{"query": "test"}'}}]},
            {"role": "assistant", "content": "Final Response"}
        ]
        mock_search.return_value = "context"
        mock_input.side_effect = ["trigger tool", ".exit"]
        
        with patch("sys.stdout"), patch("mini_copilot.main.time.monotonic", return_value=0):
            main.main()

    def test_load_github_token(self):
        with patch("mini_copilot.main.CONFIG_PATH") as mock_path:
            mock_path.exists.return_value = True
            mock_path.read_text.return_value = '{"github_token": "abc"}'
            self.assertEqual(main.load_github_token(), "abc")
            
            mock_path.exists.return_value = False
            self.assertIsNone(main.load_github_token())


if __name__ == "__main__":
    unittest.main()
