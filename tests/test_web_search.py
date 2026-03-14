import unittest
from unittest.mock import MagicMock, patch
from iclaw import web_search


class TestWebSearch(unittest.TestCase):
    @patch("iclaw.web_search.requests.get")
    def test_search_ddg(self, mock_get):
        # Match the .result__title .result__a selector
        mock_get.return_value = MagicMock(
            ok=True,
            text='<html><div class="result__title"><a class="result__a" href="u">T</a></div></html>',
        )
        results = web_search.search_ddg("q", num_results=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "u")

    @patch("iclaw.web_search.requests.get")
    def test_search_startpage(self, mock_get):
        # Match the .result and a.result-link, .wgl-title selectors
        mock_get.return_value = MagicMock(
            ok=True,
            text='<html><div class="result"><a class="result-link" href="http://u"><div class="wgl-title">T</div></a></div></html>',
        )
        results = web_search.search_startpage("q", num_results=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "http://u")
        self.assertEqual(results[0]["title"], "T")

    @patch("iclaw.web_search.requests.Session")
    def test_search_bing(self, mock_session):
        # Match the li.b_algo and h2 a selectors
        mock_s = MagicMock()
        mock_session.return_value = mock_s
        mock_s.get.return_value = MagicMock(
            ok=True,
            text='<html><li class="b_algo"><h2><a href="http://u">T</a></h2></li></html>',
        )
        results = web_search.search_bing("q", num_results=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "http://u")
        self.assertEqual(results[0]["title"], "T")

    @patch("iclaw.web_search.requests.Session")
    def test_extract_text(self, mock_session):
        mock_s = MagicMock()
        mock_session.return_value = mock_s
        mock_s.get.return_value = MagicMock(
            ok=True,
            status_code=200,
            text='<html><div id="firstHeading">T</div></html>',
            apparent_encoding="u8",
        )
        mock_s.get.return_value.apparent_encoding = "u8"
        self.assertIn(
            "T", web_search.extract_text_from_url("https://en.wikipedia.org/wiki/T")
        )


if __name__ == "__main__":
    unittest.main()
