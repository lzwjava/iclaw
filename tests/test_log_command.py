import unittest
from io import StringIO
from unittest.mock import patch

from iclaw import log
from iclaw.commands.log import handle_log_command


class TestLogCommand(unittest.TestCase):
    def setUp(self):
        log.set_level(log.VERBOSE)

    def test_no_arg_shows_current_level(self):
        with patch("sys.stdout", new_callable=StringIO) as out:
            handle_log_command(None)
        self.assertIn("verbose", out.getvalue())

    def test_set_verbose(self):
        log.set_level(log.INFO)
        with patch("sys.stdout", new_callable=StringIO) as out:
            handle_log_command("verbose")
        self.assertEqual(log.get_level(), log.VERBOSE)
        self.assertIn("verbose", out.getvalue())

    def test_set_info(self):
        with patch("sys.stdout", new_callable=StringIO) as out:
            handle_log_command("info")
        self.assertEqual(log.get_level(), log.INFO)
        self.assertIn("info", out.getvalue())

    def test_invalid_arg(self):
        with patch("sys.stdout", new_callable=StringIO) as out:
            handle_log_command("garbage")
        self.assertIn("Unknown log level", out.getvalue())
        # Level unchanged
        self.assertEqual(log.get_level(), log.VERBOSE)


if __name__ == "__main__":
    unittest.main()
