import unittest
from iclaw.exec_tool import exec_command


class TestExecTool(unittest.TestCase):
    def test_exec_echo(self):
        output = exec_command("echo 'hello world'")
        self.assertEqual(output.strip(), "hello world")

    def test_exec_ls(self):
        output = exec_command("ls pyproject.toml")
        self.assertIn("pyproject.toml", output)

    def test_exec_error(self):
        # Depending on the system, the error message might vary, but it should contain some indication of failure
        output = exec_command("non_existent_command_12345")
        self.assertIn("not found", output.lower())


if __name__ == "__main__":
    unittest.main()
