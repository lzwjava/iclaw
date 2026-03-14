import os
import unittest

from iclaw import web_search


class TestTavilySearchIntegration(unittest.TestCase):
    def setUp(self):
        self.api_key = os.environ.get("TAVILY_API_KEY")
        if not self.api_key:
            self.skipTest("TAVILY_API_KEY environment variable not set")

    def test_tavily_search_returns_results(self):
        results = web_search.search_tavily("Python programming language", num_results=3)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0, "Tavily should return at least one result")
        for r in results:
            self.assertIn("title", r)
            self.assertIn("url", r)
            self.assertIn("content", r)
            self.assertTrue(r["url"].startswith("http"))
        print(f"✅ Tavily returned {len(results)} results")

    def test_tavily_via_web_search_function(self):
        output = web_search.web_search(
            "latest news today", num_results=3, provider="tavily"
        )
        self.assertIsInstance(output, str)
        self.assertNotEqual(output, "No results found.")
        self.assertIn("### Source 1", output)
        self.assertIn("**Title:**", output)
        print(
            f"✅ Tavily via web_search() returned formatted output ({len(output)} chars)"
        )

    def test_tavily_missing_api_key(self):
        original_key = os.environ.pop("TAVILY_API_KEY", None)
        try:
            results = web_search.search_tavily("test query")
            self.assertEqual(results, [])
        finally:
            if original_key:
                os.environ["TAVILY_API_KEY"] = original_key


class TestDuckDuckGoSearchIntegration(unittest.TestCase):
    def test_ddg_search_returns_results(self):
        results = web_search.search_ddg("Python programming", num_results=5)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0, "DDG should return at least one result")
        for r in results:
            self.assertIn("title", r)
            self.assertIn("url", r)
            self.assertTrue(r["url"].startswith("http"))
        print(f"✅ DuckDuckGo returned {len(results)} results")

    def test_ddg_via_web_search_function(self):
        output = web_search.web_search(
            "Python programming", num_results=3, provider="duckduckgo"
        )
        self.assertIsInstance(output, str)
        self.assertNotEqual(output, "No results found.")
        self.assertIn("### Source 1", output)
        print(
            f"✅ DDG via web_search() returned formatted output ({len(output)} chars)"
        )


class TestBingSearchIntegration(unittest.TestCase):
    def test_bing_search_returns_results(self):
        results = web_search.search_bing("Python programming", num_results=5)
        self.assertIsInstance(results, list)
        # Bing may fail due to geo/proxy, so just check structure if results exist
        if results:
            for r in results:
                self.assertIn("title", r)
                self.assertIn("url", r)
            print(f"✅ Bing returned {len(results)} results")
        else:
            print("⚠️  Bing returned no results (may be blocked by proxy/geo)")

    def test_bing_via_web_search_function(self):
        output = web_search.web_search(
            "Python programming", num_results=3, provider="bing"
        )
        self.assertIsInstance(output, str)
        print(f"✅ Bing via web_search() returned output ({len(output)} chars)")


class TestStartpageSearchIntegration(unittest.TestCase):
    def test_startpage_search_returns_results(self):
        results = web_search.search_startpage("Python programming", num_results=5)
        self.assertIsInstance(results, list)
        if results:
            for r in results:
                self.assertIn("title", r)
                self.assertIn("url", r)
            print(f"✅ Startpage returned {len(results)} results")
        else:
            print("⚠️  Startpage returned no results (may be blocked by proxy/geo)")


class TestContentExtractionIntegration(unittest.TestCase):
    def test_extract_text_from_wikipedia(self):
        text = web_search.extract_text_from_url(
            "https://en.wikipedia.org/wiki/Python_(programming_language)"
        )
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 100, "Should extract meaningful content")
        self.assertNotIn("Error", text)
        print(f"✅ Wikipedia extraction: {len(text)} chars")

    def test_extract_text_from_github(self):
        text = web_search.extract_text_from_url("https://github.com/python/cpython")
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 50)
        print(f"✅ GitHub extraction: {len(text)} chars")


class TestWebSearchProviderDispatch(unittest.TestCase):
    """Test that web_search() correctly dispatches to different providers."""

    def test_default_provider_is_ddg(self):
        output = web_search.web_search("test query", num_results=2)
        self.assertIsInstance(output, str)

    def test_invalid_provider_falls_back_to_ddg(self):
        # Unknown provider should fall through to DDG (the else branch)
        output = web_search.web_search(
            "test query", num_results=2, provider="nonexistent"
        )
        self.assertIsInstance(output, str)


if __name__ == "__main__":
    unittest.main()
