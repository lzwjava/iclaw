import unittest
from unittest.mock import patch

from iclaw import http


class TestHttpSession(unittest.TestCase):
    def setUp(self):
        http._session = None

    def test_get_session_returns_session(self):
        with patch(
            "iclaw.http.load_session_settings",
            return_value={
                "proxy": None,
                "ca_bundle": None,
                "model_provider": "copilot",
                "current_model": "gpt-4o",
                "search_provider": "duckduckgo",
            },
        ):
            s = http.get_session()
        self.assertFalse(s.trust_env)
        self.assertEqual(s.proxies, {})
        self.assertTrue(s.verify)

    def test_get_session_with_proxy(self):
        with patch(
            "iclaw.http.load_session_settings",
            return_value={
                "proxy": "http://proxy:8080",
                "ca_bundle": None,
                "model_provider": "copilot",
                "current_model": "gpt-4o",
                "search_provider": "duckduckgo",
            },
        ):
            s = http.get_session()
        self.assertEqual(
            s.proxies, {"http": "http://proxy:8080", "https": "http://proxy:8080"}
        )

    def test_get_session_with_ca_bundle(self):
        with patch(
            "iclaw.http.load_session_settings",
            return_value={
                "proxy": None,
                "ca_bundle": "/path/cert.pem",
                "model_provider": "copilot",
                "current_model": "gpt-4o",
                "search_provider": "duckduckgo",
            },
        ):
            s = http.get_session()
        self.assertEqual(s.verify, "/path/cert.pem")

    def test_reconfigure_updates_session(self):
        with patch(
            "iclaw.http.load_session_settings",
            return_value={
                "proxy": None,
                "ca_bundle": None,
                "model_provider": "copilot",
                "current_model": "gpt-4o",
                "search_provider": "duckduckgo",
            },
        ):
            s = http.get_session()
        self.assertEqual(s.proxies, {})
        http.reconfigure(proxy="http://new:1234", ca_bundle="/new/cert.pem")
        self.assertEqual(
            s.proxies, {"http": "http://new:1234", "https": "http://new:1234"}
        )
        self.assertEqual(s.verify, "/new/cert.pem")

    def test_reconfigure_clears_settings(self):
        with patch(
            "iclaw.http.load_session_settings",
            return_value={
                "proxy": "http://proxy:8080",
                "ca_bundle": "/cert.pem",
                "model_provider": "copilot",
                "current_model": "gpt-4o",
                "search_provider": "duckduckgo",
            },
        ):
            s = http.get_session()
        http.reconfigure(proxy=None, ca_bundle=None)
        self.assertEqual(s.proxies, {})
        self.assertTrue(s.verify)

    def test_get_session_is_lazy_singleton(self):
        with patch(
            "iclaw.http.load_session_settings",
            return_value={
                "proxy": None,
                "ca_bundle": None,
                "model_provider": "copilot",
                "current_model": "gpt-4o",
                "search_provider": "duckduckgo",
            },
        ):
            s1 = http.get_session()
            s2 = http.get_session()
        self.assertIs(s1, s2)


if __name__ == "__main__":
    unittest.main()
