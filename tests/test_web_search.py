import unittest
from unittest.mock import MagicMock, patch
from mini_copilot import web_search

class TestWebSearch(unittest.TestCase):
    @patch("mini_copilot.web_search.requests.get")
    def test_search_ddg(self, mock_get):
        # Match the .result__title .result__a selector
        mock_get.return_value = MagicMock(ok=True, text='<html><div class="result__title"><a class="result__a" href="u">T</a></div></html>')
        results = web_search.search_ddg("q", num_results=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "u")

    @patch("mini_copilot.web_search.requests.Session")
    def test_extract_text(self, mock_session):
        mock_s = MagicMock()
        mock_session.return_value = mock_s
        mock_s.get.return_value = MagicMock(ok=True, status_code=200, text='<html><div id="firstHeading">T</div></html>', apparent_encoding='u8')
        mock_s.get.return_value.apparent_encoding = 'u8'
        self.assertIn("T", web_search.extract_text_from_url("https://en.wikipedia.org/wiki/T"))

if __name__ == "__main__":
    unittest.main()
