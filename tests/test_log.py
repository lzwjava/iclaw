import unittest
from io import StringIO
from unittest.mock import patch

from iclaw import log


class TestLog(unittest.TestCase):
    def setUp(self):
        log.set_level(log.VERBOSE)

    def test_log_info_always_prints(self):
        log.set_level(log.INFO)
        with patch("sys.stdout", new_callable=StringIO) as out:
            log.log_info("hello")
        self.assertEqual(out.getvalue(), "hello\n")

    def test_log_verbose_prints_in_verbose_mode(self):
        log.set_level(log.VERBOSE)
        with patch("sys.stdout", new_callable=StringIO) as out:
            log.log_verbose("debug msg")
        self.assertEqual(out.getvalue(), "debug msg\n")

    def test_log_verbose_suppressed_in_info_mode(self):
        log.set_level(log.INFO)
        with patch("sys.stdout", new_callable=StringIO) as out:
            log.log_verbose("debug msg")
        self.assertEqual(out.getvalue(), "")

    def test_get_level_returns_current(self):
        log.set_level(log.INFO)
        self.assertEqual(log.get_level(), log.INFO)
        log.set_level(log.VERBOSE)
        self.assertEqual(log.get_level(), log.VERBOSE)

    def test_level_name(self):
        self.assertEqual(log.level_name(log.INFO), "info")
        self.assertEqual(log.level_name(log.VERBOSE), "verbose")


if __name__ == "__main__":
    unittest.main()
