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
    def test_handle_login_command(self, mock_poll, mock_device):
        mock_device.return_value = {"device_code": "dc"}
        mock_poll.return_value = "at"
        mock_path = MagicMock()
        with patch("sys.stdout"):
            res = auth.handle_login_command(mock_path, 1)
        self.assertEqual(res, "at")

    @patch("iclaw.commands.utils.sys")
    def test_handle_copy_command(self, mock_sys):
        # We'll patch pyperclip inside sys.modules because it's imported inside the function
        mock_py = MagicMock()
        with patch.dict("sys.modules", {"pyperclip": mock_py}):
            with patch("sys.stdout"):
                utils.handle_copy_command("text")
        mock_py.copy.assert_called_with("text")

if __name__ == "__main__":
    unittest.main()
