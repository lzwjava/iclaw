import unittest
from unittest.mock import MagicMock, patch
from iclaw.commands import model, search_provider, auth, utils


class TestCommands(unittest.TestCase):
    @patch("iclaw.commands.model.get_models")
    @patch("iclaw.commands.model.input", return_value="1")
    def test_handle_model_command(self, mock_input, mock_models):
        mock_models.return_value = [{"id": "m1", "owned_by": "o1"}]
        with patch("sys.stdout"):
            res = model.handle_model_command("t", "curr")
        self.assertEqual(res, "m1")

    @patch("iclaw.commands.search_provider.input", return_value="1")
    def test_handle_search_provider_command(self, mock_input):
        with patch("sys.stdout"):
            res = search_provider.handle_search_provider_command("duckduckgo")
        self.assertEqual(res, "duckduckgo")

    @patch("iclaw.commands.auth.get_device_code")
    @patch("iclaw.commands.auth.poll_for_access_token")
    @patch("iclaw.commands.auth.input", return_value="1")
    def test_handle_login_command(self, mock_input, mock_poll, mock_device):
        mock_device.return_value = {"device_code": "dc", "interval": 5}
        mock_poll.return_value = "at"
        mock_path = MagicMock()
        with patch("sys.stdout"):
            res = auth.handle_login_command(mock_path)
        self.assertEqual(res, "at")

    @patch("iclaw.commands.utils.sys")
    def test_handle_copy_command(self, mock_sys):
        mock_py = MagicMock()
        with patch.dict("sys.modules", {"pyperclip": mock_py}):
            with patch("sys.stdout"):
                utils.handle_copy_command("text")
        mock_py.copy.assert_called_with("text")

    # --- New tests for model.py ---

    def test_handle_model_command_no_token(self):
        with patch("sys.stderr"):
            res = model.handle_model_command(None, "gpt-4o")
        self.assertEqual(res, "gpt-4o")

    @patch("iclaw.commands.model.get_models", side_effect=Exception("fail"))
    def test_handle_model_command_fetch_error(self, mock_models):
        with patch("sys.stderr"):
            res = model.handle_model_command("t", "gpt-4o")
        self.assertEqual(res, "gpt-4o")

    @patch("iclaw.commands.model.get_models")
    @patch("iclaw.commands.model.input", return_value="")
    def test_handle_model_command_empty_input(self, mock_input, mock_models):
        mock_models.return_value = [{"id": "m1", "owned_by": "o1"}]
        with patch("sys.stdout"):
            res = model.handle_model_command("t", "curr")
        self.assertEqual(res, "curr")

    @patch("iclaw.commands.model.get_models")
    @patch("iclaw.commands.model.input", return_value="m1")
    def test_handle_model_command_by_name(self, mock_input, mock_models):
        mock_models.return_value = [{"id": "m1", "owned_by": "o1"}]
        with patch("sys.stdout"):
            res = model.handle_model_command("t", "curr")
        self.assertEqual(res, "m1")

    @patch("iclaw.commands.model.get_models")
    @patch("iclaw.commands.model.input", return_value="999")
    def test_handle_model_command_invalid_number(self, mock_input, mock_models):
        mock_models.return_value = [{"id": "m1", "owned_by": "o1"}]
        with patch("sys.stdout"):
            res = model.handle_model_command("t", "curr")
        self.assertEqual(res, "curr")

    @patch("iclaw.commands.model.get_models")
    @patch("iclaw.commands.model.input", return_value="nonexistent")
    def test_handle_model_command_unknown_name(self, mock_input, mock_models):
        mock_models.return_value = [{"id": "m1", "owned_by": "o1"}]
        with patch("sys.stdout"):
            res = model.handle_model_command("t", "curr")
        self.assertEqual(res, "curr")

    @patch("iclaw.commands.model.get_models")
    @patch("iclaw.commands.model.input", side_effect=EOFError)
    def test_handle_model_command_eof(self, mock_input, mock_models):
        mock_models.return_value = [{"id": "m1", "owned_by": "o1"}]
        with patch("sys.stdout"):
            res = model.handle_model_command("t", "curr")
        self.assertEqual(res, "curr")

    # --- New tests for model_provider ---

    @patch("iclaw.commands.model.input", return_value="")
    def test_model_provider_empty_input(self, mock_input):
        with patch("sys.stdout"):
            p, t = model.handle_model_provider_command(MagicMock(), "copilot")
        self.assertEqual(p, "copilot")
        self.assertIsNone(t)

    @patch("iclaw.commands.model.handle_login_command", return_value="gh_tok")
    @patch("iclaw.commands.model.get_copilot_token", return_value="cp_tok")
    @patch("iclaw.commands.model.input", return_value="1")
    def test_model_provider_copilot_success(self, mock_input, mock_cp, mock_login):
        with patch("sys.stdout"):
            p, t = model.handle_model_provider_command(MagicMock(), "copilot")
        self.assertEqual(p, "copilot")
        self.assertEqual(t, "cp_tok")

    @patch("iclaw.commands.model.handle_login_command", return_value="gh_tok")
    @patch("iclaw.commands.model.get_copilot_token", side_effect=Exception("err"))
    @patch("iclaw.commands.model.input", return_value="1")
    def test_model_provider_copilot_error(self, mock_input, mock_cp, mock_login):
        with patch("sys.stdout"), patch("sys.stderr"):
            p, t = model.handle_model_provider_command(MagicMock(), "copilot")
        self.assertEqual(p, "copilot")
        self.assertIsNone(t)

    @patch("iclaw.commands.model.handle_login_command", return_value=None)
    @patch("iclaw.commands.model.input", return_value="1")
    def test_model_provider_copilot_no_github_token(self, mock_input, mock_login):
        with patch("sys.stdout"):
            p, t = model.handle_model_provider_command(MagicMock(), "copilot")
        self.assertEqual(p, "copilot")
        self.assertIsNone(t)

    @patch("iclaw.commands.model.load_openrouter_api_key", return_value="env_key")
    @patch("iclaw.commands.model.input", return_value="2")
    def test_model_provider_openrouter_from_env(self, mock_input, mock_key):
        with patch("sys.stdout"):
            p, t = model.handle_model_provider_command(MagicMock(), "copilot")
        self.assertEqual(p, "openrouter")
        self.assertEqual(t, "env_key")

    @patch("iclaw.commands.model.save_openrouter_api_key")
    @patch("iclaw.commands.model.load_openrouter_api_key", return_value=None)
    @patch("iclaw.commands.model.input", side_effect=["2", "typed_key"])
    def test_model_provider_openrouter_prompt(self, mock_input, mock_key, mock_save):
        with patch("sys.stdout"):
            p, t = model.handle_model_provider_command(MagicMock(), "copilot")
        self.assertEqual(p, "openrouter")
        self.assertEqual(t, "typed_key")
        mock_save.assert_called_once_with("typed_key")

    @patch("iclaw.commands.model.input", return_value="99")
    def test_model_provider_invalid(self, mock_input):
        with patch("sys.stdout"):
            p, t = model.handle_model_provider_command(MagicMock(), "copilot")
        self.assertEqual(p, "copilot")
        self.assertIsNone(t)

    # --- New tests for search_provider ---

    @patch("iclaw.commands.search_provider.input", return_value="2")
    def test_search_provider_select_startpage(self, mock_input):
        with patch("sys.stdout"):
            res = search_provider.handle_search_provider_command("duckduckgo")
        self.assertEqual(res, "startpage")

    @patch("iclaw.commands.search_provider.input", return_value="99")
    def test_search_provider_invalid_number(self, mock_input):
        with patch("sys.stdout"):
            res = search_provider.handle_search_provider_command("duckduckgo")
        self.assertEqual(res, "duckduckgo")

    @patch("iclaw.commands.search_provider.input", return_value="abc")
    def test_search_provider_not_a_number(self, mock_input):
        with patch("sys.stdout"):
            res = search_provider.handle_search_provider_command("duckduckgo")
        self.assertEqual(res, "duckduckgo")

    @patch("iclaw.commands.search_provider.input", return_value="")
    def test_search_provider_empty(self, mock_input):
        with patch("sys.stdout"):
            res = search_provider.handle_search_provider_command("duckduckgo")
        self.assertEqual(res, "duckduckgo")

    @patch("iclaw.commands.search_provider.os.getenv", return_value=None)
    @patch("iclaw.commands.search_provider.input", side_effect=["4", "mykey"])
    def test_search_provider_tavily_with_key(self, mock_input, mock_getenv):
        with patch("sys.stdout"):
            res = search_provider.handle_search_provider_command("duckduckgo")
        self.assertEqual(res, "tavily")

    @patch("iclaw.commands.search_provider.os.getenv", return_value=None)
    @patch("iclaw.commands.search_provider.input", side_effect=["4", ""])
    def test_search_provider_tavily_no_key(self, mock_input, mock_getenv):
        with patch("sys.stdout"):
            res = search_provider.handle_search_provider_command("duckduckgo")
        self.assertEqual(res, "duckduckgo")

    @patch("iclaw.commands.search_provider.input", side_effect=EOFError)
    def test_search_provider_eof(self, mock_input):
        with patch("sys.stdout"):
            res = search_provider.handle_search_provider_command("duckduckgo")
        self.assertEqual(res, "duckduckgo")

    # --- New tests for auth ---

    @patch("iclaw.commands.auth.input", return_value="2")
    def test_login_direct_token(self, mock_input):
        mock_input.side_effect = ["2", "my_token"]
        mock_path = MagicMock()
        with patch("sys.stdout"):
            res = auth.handle_login_command(mock_path)
        self.assertEqual(res, "my_token")

    @patch("iclaw.commands.auth.input", side_effect=["2", ""])
    def test_login_direct_token_empty(self, mock_input):
        mock_path = MagicMock()
        with patch("sys.stdout"):
            res = auth.handle_login_command(mock_path)
        self.assertIsNone(res)

    @patch("iclaw.commands.auth.input", return_value="3")
    def test_login_invalid_choice(self, mock_input):
        mock_path = MagicMock()
        with patch("sys.stdout"):
            res = auth.handle_login_command(mock_path)
        self.assertIsNone(res)

    @patch("iclaw.commands.auth.get_device_code", side_effect=Exception("net err"))
    @patch("iclaw.commands.auth.input", return_value="1")
    def test_login_device_flow_error(self, mock_input, mock_device):
        mock_path = MagicMock()
        with patch("sys.stdout"), patch("sys.stderr"):
            res = auth.handle_login_command(mock_path)
        self.assertIsNone(res)

    # --- New tests for utils ---

    def test_copy_nothing(self):
        with patch("sys.stdout"):
            utils.handle_copy_command(None)

    def test_copy_exception(self):
        with patch.dict("sys.modules", {"pyperclip": None}):
            with patch("sys.stderr"), patch("sys.stdout"):
                utils.handle_copy_command("text")


if __name__ == "__main__":
    unittest.main()
