import json
import unittest
from unittest.mock import patch, MagicMock

from iclaw.config import load_session_settings, save_session_settings


class TestConfigProxySettings(unittest.TestCase):
    def test_load_defaults_when_no_proxy_or_ca_bundle(self):
        with patch("iclaw.config.CONFIG_PATH") as mp:
            mp.exists.return_value = True
            mp.read_text.return_value = json.dumps({"model_provider": "copilot"})
            settings = load_session_settings()
        self.assertIsNone(settings["proxy"])
        self.assertIsNone(settings["ca_bundle"])

    def test_load_proxy_and_ca_bundle_when_set(self):
        with patch("iclaw.config.CONFIG_PATH") as mp:
            mp.exists.return_value = True
            mp.read_text.return_value = json.dumps(
                {
                    "proxy": "http://127.0.0.1:8080",
                    "ca_bundle": "/path/to/cert.pem",
                }
            )
            settings = load_session_settings()
        self.assertEqual(settings["proxy"], "http://127.0.0.1:8080")
        self.assertEqual(settings["ca_bundle"], "/path/to/cert.pem")

    def test_save_session_settings_with_proxy_and_ca_bundle(self):
        with patch("iclaw.config.CONFIG_PATH") as mp:
            mp.exists.return_value = True
            mp.read_text.return_value = json.dumps({"github_token": "gt"})
            mp.parent = MagicMock()
            save_session_settings(
                model_provider="copilot",
                current_model="gpt-4o",
                search_provider="duckduckgo",
                proxy="http://proxy:8080",
                ca_bundle="/path/cert.pem",
            )
            written = json.loads(mp.write_text.call_args[0][0])
        self.assertEqual(written["proxy"], "http://proxy:8080")
        self.assertEqual(written["ca_bundle"], "/path/cert.pem")
        self.assertEqual(written["github_token"], "gt")

    def test_save_session_settings_clears_null_proxy(self):
        with patch("iclaw.config.CONFIG_PATH") as mp:
            mp.exists.return_value = True
            mp.read_text.return_value = json.dumps({"proxy": "http://old:1234"})
            mp.parent = MagicMock()
            save_session_settings(
                model_provider="copilot",
                current_model="gpt-4o",
                search_provider="duckduckgo",
                proxy=None,
                ca_bundle=None,
            )
            written = json.loads(mp.write_text.call_args[0][0])
        self.assertIsNone(written["proxy"])
        self.assertIsNone(written["ca_bundle"])


if __name__ == "__main__":
    unittest.main()
