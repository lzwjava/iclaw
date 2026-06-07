import unittest
from unittest.mock import patch

from iclaw.safety import check_edit_safety, check_exec_safety


class TestSafetyLevelLow(unittest.TestCase):
    """When safety is 'low', everything is allowed."""

    def test_low_allows_rm_root(self):
        self.assertIsNone(check_exec_safety("rm -rf /", "low"))

    def test_low_allows_edit_outside(self):
        self.assertIsNone(check_edit_safety("/etc/passwd", "low"))


class TestCheckExecSafetyHigh(unittest.TestCase):
    """When safety is 'high', destructive ops outside CWD are blocked."""

    def test_allows_ls_anywhere(self):
        self.assertIsNone(check_exec_safety("ls /etc", "high"))

    def test_allows_cat_anywhere(self):
        self.assertIsNone(check_exec_safety("cat /etc/passwd", "high"))

    def test_allows_pip_install(self):
        self.assertIsNone(check_exec_safety("pip install requests", "high"))

    def test_allows_python_script(self):
        self.assertIsNone(check_exec_safety("python3 main.py", "high"))

    def test_allows_git_commands(self):
        self.assertIsNone(check_exec_safety("git push origin main", "high"))

    def test_allows_rm_inside_cwd(self):
        with patch("iclaw.safety.os.getcwd", return_value="/home/user/project"):
            with patch(
                "iclaw.safety.os.path.realpath",
                side_effect=lambda p: p,
            ):
                self.assertIsNone(
                    check_exec_safety("rm -rf /home/user/project/build", "high")
                )

    def test_blocks_rm_outside_cwd(self):
        with patch("iclaw.safety.os.getcwd", return_value="/home/user/project"):
            with patch(
                "iclaw.safety.os.path.realpath",
                side_effect=lambda p: p,
            ):
                result = check_exec_safety("rm -rf /etc/important", "high")
                self.assertIsNotNone(result)
                self.assertIn("Safety HIGH", result)

    def test_blocks_mv_outside_cwd(self):
        with patch("iclaw.safety.os.getcwd", return_value="/home/user/project"):
            with patch(
                "iclaw.safety.os.path.realpath",
                side_effect=lambda p: p,
            ):
                result = check_exec_safety(
                    "mv /home/user/project/file.txt /tmp/file.txt", "high"
                )
                self.assertIsNotNone(result)
                self.assertIn("Safety HIGH", result)

    def test_blocks_cp_to_outside_cwd(self):
        with patch("iclaw.safety.os.getcwd", return_value="/home/user/project"):
            with patch(
                "iclaw.safety.os.path.realpath",
                side_effect=lambda p: p,
            ):
                result = check_exec_safety("cp file.txt /etc/file.txt", "high")
                self.assertIsNotNone(result)
                self.assertIn("Safety HIGH", result)

    def test_blocks_rm_with_sudo(self):
        with patch("iclaw.safety.os.getcwd", return_value="/home/user/project"):
            with patch(
                "iclaw.safety.os.path.realpath",
                side_effect=lambda p: p,
            ):
                result = check_exec_safety("sudo rm -rf /var/log", "high")
                self.assertIsNotNone(result)

    def test_blocks_rm_dev_null_outside_cwd(self):
        """rm /dev/null is blocked in high mode since it's outside CWD."""
        with patch("iclaw.safety.os.getcwd", return_value="/home/user/project"):
            result = check_exec_safety("rm /dev/null", "high")
            self.assertIsNotNone(result)


class TestCheckEditSafetyHigh(unittest.TestCase):
    """When safety is 'high', edits outside CWD are blocked."""

    def test_allows_edit_inside_cwd(self):
        with patch("iclaw.safety.os.getcwd", return_value="/home/user/project"):
            with patch(
                "iclaw.safety.os.path.realpath",
                side_effect=lambda p: p,
            ):
                self.assertIsNone(
                    check_edit_safety("/home/user/project/main.py", "high")
                )

    def test_blocks_edit_outside_cwd(self):
        with patch("iclaw.safety.os.getcwd", return_value="/home/user/project"):
            with patch(
                "iclaw.safety.os.path.realpath",
                side_effect=lambda p: p,
            ):
                result = check_edit_safety("/etc/passwd", "high")
                self.assertIsNotNone(result)
                self.assertIn("Safety HIGH", result)

    def test_blocks_edit_relative_outside_cwd(self):
        cwd = "/home/user/project"
        with patch("iclaw.safety.os.getcwd", return_value=cwd):
            # Don't mock realpath — let it resolve naturally
            result = check_edit_safety("../../etc/passwd", "high")
            self.assertIsNotNone(result)

    def test_allows_edit_low(self):
        self.assertIsNone(check_edit_safety("/etc/passwd", "low"))


if __name__ == "__main__":
    unittest.main()
