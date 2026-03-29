import unittest
from unittest.mock import MagicMock, patch
from iclaw import web_search


class TestWebSearch(unittest.TestCase):
    @patch("iclaw.web_search.http.get_session")
    def test_search_ddg(self, mock_gs):
        mock_session = MagicMock()
        mock_gs.return_value = mock_session
        mock_session.get.return_value = MagicMock(
            ok=True,
            text='<html><div class="result__title"><a class="result__a" href="u">T</a></div></html>',
        )
        results = web_search.search_ddg("q", num_results=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "u")

    @patch("iclaw.web_search.http.get_session")
    def test_search_ddg_with_redirect_url(self, mock_gs):
        mock_session = MagicMock()
        mock_gs.return_value = mock_session
        mock_session.get.return_value = MagicMock(
            ok=True,
            text='<html><div class="result__title"><a class="result__a" href="//duckduckgo.com/l/?uddg=http%3A%2F%2Fexample.com">T</a></div></html>',
        )
        results = web_search.search_ddg("q", num_results=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "http://example.com")

    @patch("iclaw.web_search.http.get_session")
    def test_search_ddg_double_slash_url(self, mock_gs):
        mock_session = MagicMock()
        mock_gs.return_value = mock_session
        mock_session.get.return_value = MagicMock(
            ok=True,
            text='<html><div class="result__title"><a class="result__a" href="//example.com/page">T</a></div></html>',
        )
        results = web_search.search_ddg("q", num_results=1)
        self.assertEqual(results[0]["url"], "https://example.com/page")

    @patch("iclaw.web_search.http.get_session")
    def test_search_ddg_error(self, mock_gs):
        mock_gs.return_value.get.side_effect = Exception("network error")
        with patch("sys.stdout"):
            results = web_search.search_ddg("q")
        self.assertEqual(results, [])

    @patch("iclaw.web_search.http.get_session")
    def test_search_startpage(self, mock_gs):
        mock_session = MagicMock()
        mock_gs.return_value = mock_session
        mock_session.get.return_value = MagicMock(
            ok=True,
            text='<html><div class="result"><a class="result-link" href="http://u"><div class="wgl-title">T</div></a></div></html>',
        )
        results = web_search.search_startpage("q", num_results=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "http://u")
        self.assertEqual(results[0]["title"], "T")

    @patch("iclaw.web_search.http.get_session")
    def test_search_startpage_error(self, mock_gs):
        mock_gs.return_value.get.side_effect = Exception("err")
        with patch("sys.stdout"):
            results = web_search.search_startpage("q")
        self.assertEqual(results, [])

    @patch("iclaw.web_search.http.get_session")
    @patch("iclaw.web_search.requests.Session")
    def test_search_bing(self, mock_session, mock_gs):
        mock_shared = MagicMock()
        mock_shared.proxies = {}
        mock_shared.verify = True
        mock_gs.return_value = mock_shared
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

    @patch("iclaw.web_search.http.get_session")
    @patch("iclaw.web_search.requests.Session")
    def test_search_bing_double_slash(self, mock_session, mock_gs):
        mock_shared = MagicMock()
        mock_shared.proxies = {}
        mock_shared.verify = True
        mock_gs.return_value = mock_shared
        mock_s = MagicMock()
        mock_session.return_value = mock_s
        mock_s.get.return_value = MagicMock(
            ok=True,
            text='<html><li class="b_algo"><h2><a href="//u.com">T</a></h2></li></html>',
        )
        results = web_search.search_bing("q", num_results=1)
        self.assertEqual(results[0]["url"], "https://u.com")

    @patch("iclaw.web_search.http.get_session")
    @patch("iclaw.web_search.requests.Session")
    def test_search_bing_error(self, mock_session, mock_gs):
        mock_shared = MagicMock()
        mock_shared.proxies = {}
        mock_shared.verify = True
        mock_gs.return_value = mock_shared
        mock_s = MagicMock()
        mock_session.return_value = mock_s
        mock_s.get.side_effect = Exception("err")
        with patch("sys.stdout"):
            results = web_search.search_bing("q")
        self.assertEqual(results, [])

    @patch("iclaw.web_search.http.get_session")
    def test_extract_text(self, mock_gs):
        mock_session = MagicMock()
        mock_gs.return_value = mock_session
        mock_session.get.return_value = MagicMock(
            ok=True,
            status_code=200,
            text='<html><div id="firstHeading">T</div></html>',
            apparent_encoding="u8",
        )
        self.assertIn(
            "T", web_search.extract_text_from_url("https://en.wikipedia.org/wiki/T")
        )

    @patch("iclaw.web_search.http.get_session")
    def test_extract_text_non_200(self, mock_gs):
        mock_session = MagicMock()
        mock_gs.return_value = mock_session
        mock_session.get.return_value = MagicMock(
            status_code=404, apparent_encoding="utf-8"
        )
        result = web_search.extract_text_from_url("http://example.com")
        self.assertIn("404", result)

    @patch("iclaw.web_search.http.get_session")
    def test_extract_text_exception(self, mock_gs):
        mock_session = MagicMock()
        mock_gs.return_value = mock_session
        mock_session.get.side_effect = Exception("timeout")
        result = web_search.extract_text_from_url("http://example.com")
        self.assertIn("Error", result)

    @patch("iclaw.web_search.http.get_session")
    def test_extract_text_zhihu(self, mock_gs):
        mock_session = MagicMock()
        mock_gs.return_value = mock_session
        mock_session.get.return_value = MagicMock(
            status_code=200,
            text='<html><body><h1 class="QuestionHeader-title">Question</h1><div class="RichContent-inner">Answer text</div></body></html>',
            apparent_encoding="utf-8",
        )
        result = web_search.extract_text_from_url("https://zhihu.com/question/123")
        self.assertIn("Question", result)

    @patch("iclaw.web_search.http.get_session")
    def test_extract_text_github(self, mock_gs):
        mock_session = MagicMock()
        mock_gs.return_value = mock_session
        mock_session.get.return_value = MagicMock(
            status_code=200,
            text='<html><body><div class="repository-content">Repo content here</div></body></html>',
            apparent_encoding="utf-8",
        )
        result = web_search.extract_text_from_url("https://github.com/user/repo")
        self.assertIn("Repo content", result)

    @patch("iclaw.web_search.http.get_session")
    def test_extract_text_baidu_zhidao(self, mock_gs):
        mock_session = MagicMock()
        mock_gs.return_value = mock_session
        mock_session.get.return_value = MagicMock(
            status_code=200,
            text='<html><body><div class="wgt-best-content">Best answer</div></body></html>',
            apparent_encoding="utf-8",
        )
        result = web_search.extract_text_from_url(
            "https://zhidao.baidu.com/question/123"
        )
        self.assertIn("Best answer", result)

    @patch("iclaw.web_search.Document")
    @patch("iclaw.web_search.http.get_session")
    def test_extract_text_generic_readability(self, mock_gs, mock_doc):
        mock_session = MagicMock()
        mock_gs.return_value = mock_session
        mock_session.get.return_value = MagicMock(
            status_code=200,
            text="<html><body><p>Hello world content that is long enough to pass the 100 char threshold and needs to be extracted properly by the readability library for the test to pass.</p></body></html>",
            apparent_encoding="utf-8",
        )
        mock_doc.return_value.summary.return_value = "<p>Hello world content that is long enough to pass the 100 char threshold and needs to be extracted properly by the readability library for the test to pass.</p>"
        result = web_search.extract_text_from_url("http://example.com/article")
        self.assertIn("Hello world", result)

    @patch("iclaw.web_search.Document")
    @patch("iclaw.web_search.http.get_session")
    def test_extract_text_generic_fallback(self, mock_gs, mock_doc):
        mock_session = MagicMock()
        mock_gs.return_value = mock_session
        mock_session.get.return_value = MagicMock(
            status_code=200,
            text="<html><body><main>Main content</main></body></html>",
            apparent_encoding="utf-8",
        )
        mock_doc.return_value.summary.return_value = "<p>short</p>"
        result = web_search.extract_text_from_url("http://example.com/article")
        self.assertIn("Main content", result)

    @patch("iclaw.web_search.Document")
    @patch("iclaw.web_search.http.get_session")
    def test_extract_text_body_fallback(self, mock_gs, mock_doc):
        mock_session = MagicMock()
        mock_gs.return_value = mock_session
        mock_session.get.return_value = MagicMock(
            status_code=200,
            text="<html><body><p>Body text</p></body></html>",
            apparent_encoding="utf-8",
        )
        mock_doc.return_value.summary.return_value = ""
        result = web_search.extract_text_from_url("http://example.com/page")
        self.assertIn("Body text", result)

    def test_format_llm_output(self):
        results = [
            {"title": "T1", "url": "http://u1", "content": "C1"},
            {"title": "T2", "url": "http://u2"},
        ]
        output = web_search.format_llm_output(results)
        self.assertIn("T1", output)
        self.assertIn("C1", output)
        self.assertIn("No content extracted.", output)

    @patch("iclaw.web_search.search_ddg", return_value=[])
    def test_web_search_no_results(self, mock_ddg):
        with patch("sys.stdout"):
            result = web_search.web_search("q")
        self.assertEqual(result, "No results found.")

    @patch("iclaw.web_search.extract_text_from_url", return_value="content")
    @patch(
        "iclaw.web_search.search_ddg",
        return_value=[{"title": "T", "url": "http://u"}],
    )
    def test_web_search_ddg_provider(self, mock_ddg, mock_extract):
        with patch("sys.stdout"):
            result = web_search.web_search("q", provider="duckduckgo")
        self.assertIn("T", result)

    @patch("iclaw.web_search.extract_text_from_url", return_value="content")
    @patch(
        "iclaw.web_search.search_startpage",
        return_value=[{"title": "T", "url": "http://u"}],
    )
    def test_web_search_startpage_provider(self, mock_sp, mock_extract):
        with patch("sys.stdout"):
            result = web_search.web_search("q", provider="startpage")
        self.assertIn("T", result)

    @patch("iclaw.web_search.extract_text_from_url", return_value="content")
    @patch(
        "iclaw.web_search.search_bing",
        return_value=[{"title": "T", "url": "http://u"}],
    )
    def test_web_search_bing_provider(self, mock_bing, mock_extract):
        with patch("sys.stdout"):
            result = web_search.web_search("q", provider="bing")
        self.assertIn("T", result)

    @patch("iclaw.web_search.search_tavily", return_value=[])
    def test_web_search_tavily_no_results(self, mock_tavily):
        with patch("sys.stdout"):
            result = web_search.web_search("q", provider="tavily")
        self.assertEqual(result, "No results found.")

    @patch(
        "iclaw.web_search.search_tavily",
        return_value=[{"title": "T", "url": "http://u", "content": "C"}],
    )
    def test_web_search_tavily_with_results(self, mock_tavily):
        with patch("sys.stdout"):
            result = web_search.web_search("q", provider="tavily")
        self.assertIn("T", result)

    @patch("iclaw.web_search.extract_text_from_url", side_effect=Exception("fail"))
    @patch(
        "iclaw.web_search.search_ddg",
        return_value=[{"title": "T", "url": "http://u"}],
    )
    def test_web_search_extract_failure(self, mock_ddg, mock_extract):
        with patch("sys.stdout"):
            result = web_search.web_search("q", provider="duckduckgo")
        self.assertIn("Failed to extract", result)


class TestSearchTavily(unittest.TestCase):
    @patch.dict("os.environ", {}, clear=True)
    def test_tavily_no_api_key(self):
        with patch("sys.stdout"):
            results = web_search.search_tavily("q")
        self.assertEqual(results, [])

    @patch.dict("os.environ", {"TAVILY_API_KEY": "key"})
    def test_tavily_success(self):
        mock_client = MagicMock()
        mock_client.search.return_value = {
            "results": [{"title": "T", "url": "http://u", "content": "C"}]
        }
        mock_tavily_mod = MagicMock()
        mock_tavily_mod.TavilyClient.return_value = mock_client
        with patch.dict("sys.modules", {"tavily": mock_tavily_mod}):
            results = web_search.search_tavily("q")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "T")

    @patch.dict("os.environ", {"TAVILY_API_KEY": "key"})
    def test_tavily_error(self):
        mock_tavily_mod = MagicMock()
        mock_tavily_mod.TavilyClient.side_effect = Exception("api err")
        with patch.dict("sys.modules", {"tavily": mock_tavily_mod}):
            with patch("sys.stdout"):
                results = web_search.search_tavily("q")
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
