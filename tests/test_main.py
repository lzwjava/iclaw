import unittest
from unittest.mock import MagicMock, patch
from mini_copilot import main

class TestMain(unittest.TestCase):
    @patch("mini_copilot.main.chat")
    @patch("mini_copilot.main.load_github_token")
    @patch("mini_copilot.main.input")
    def test_main_cli(self, mock_input, mock_load, mock_chat):
        mock_load.return_value = "gt"
        mock_input.side_effect = [".exit"]
        with patch("sys.stdout"), patch("mini_copilot.main.get_copilot_token"), patch("mini_copilot.main.time.monotonic", return_value=0):
            main.main()

    def test_load_github_token(self):
        with patch("mini_copilot.main.CONFIG_PATH") as mp:
            mp.exists.return_value = True
            mp.read_text.return_value = '{"github_token": "t"}'
            self.assertEqual(main.load_github_token(), "t")

if __name__ == "__main__":
    unittest.main()
