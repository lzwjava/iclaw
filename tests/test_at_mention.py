"""Integration tests for @ file mention and IclawCompleter."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document

from iclaw.at_mention import resolve_at_mentions
from iclaw.completer import IclawCompleter


class TestResolveAtMentions(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.file1 = os.path.join(self.tmpdir, "hello.txt")
        Path(self.file1).write_text("hello world")
        self.file2 = os.path.join(self.tmpdir, "other.py")
        Path(self.file2).write_text("print('hi')")

    def test_no_mentions_returns_original(self):
        text = "just a plain message"
        self.assertEqual(resolve_at_mentions(text), text)

    def test_mention_nonexistent_file_returns_original(self):
        text = "look at @nonexistent_file.txt"
        self.assertEqual(resolve_at_mentions(text), text)

    def test_mention_existing_file_prepends_contents(self):
        text = f"explain @{self.file1}"
        result = resolve_at_mentions(text)
        self.assertIn("hello world", result)
        self.assertIn(f'<file path="{self.file1}">', result)
        self.assertIn(text, result)

    def test_mention_multiple_files(self):
        text = f"compare @{self.file1} and @{self.file2}"
        result = resolve_at_mentions(text)
        self.assertIn("hello world", result)
        self.assertIn("print('hi')", result)
        self.assertIn(text, result)

    def test_file_contents_come_before_message(self):
        text = f"explain @{self.file1}"
        result = resolve_at_mentions(text)
        file_tag_pos = result.index("<file")
        msg_pos = result.index(text)
        self.assertLess(file_tag_pos, msg_pos)

    def test_mention_directory_ignored(self):
        text = f"look at @{self.tmpdir}"
        # directories are not files, so no injection
        result = resolve_at_mentions(text)
        self.assertEqual(result, text)

    def test_unreadable_file_skipped(self):
        text = f"explain @{self.file1}"
        with patch(
            "iclaw.at_mention.Path.read_text", side_effect=OSError("perm denied")
        ):
            result = resolve_at_mentions(text)
        self.assertEqual(result, text)


TEST_FILES = ["alpha.py", "alpha_test.py", "beta.txt", "subdir/gamma.py"]


class TestIclawCompleter(unittest.TestCase):
    def setUp(self):
        self.completer = IclawCompleter()
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        # Create actual files so os.path.isdir/isfile work in meta checks
        Path("alpha.py").write_text("")
        Path("alpha_test.py").write_text("")
        Path("beta.txt").write_text("")
        os.makedirs("subdir", exist_ok=True)
        Path("subdir/gamma.py").write_text("")
        # Patch _get_git_files so tests don't require a real git repo
        self.patcher = patch("iclaw.completer._get_git_files", return_value=TEST_FILES)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        os.chdir(self.orig_cwd)

    def _completions(self, text):
        doc = Document(text)
        return list(self.completer.get_completions(doc, CompleteEvent()))

    # --- @ file mention ---

    def test_at_with_no_prefix_returns_files(self):
        completions = self._completions("@")
        paths = [c.text for c in completions]
        self.assertIn("alpha.py", paths)
        self.assertIn("beta.txt", paths)

    def test_at_with_partial_prefix_filters(self):
        completions = self._completions("@alph")
        paths = [c.text for c in completions]
        self.assertTrue(all("alpha" in p for p in paths))
        self.assertNotIn("beta.txt", paths)

    def test_at_completion_replaces_prefix(self):
        completions = self._completions("@alph")
        for c in completions:
            # start_position should be negative len of "alph"
            self.assertEqual(c.start_position, -len("alph"))

    def test_at_meta_shows_file_or_dir(self):
        completions = self._completions("@")
        meta_map = {c.text: c.display_meta for c in completions}
        # display_meta is a FormattedText; convert to string for assertion
        for path, meta in meta_map.items():
            expected = "dir" if os.path.isdir(path) else "file"
            self.assertIn(expected, str(meta))

    def test_at_mid_sentence(self):
        completions = self._completions("review the file @alph")
        paths = [c.text for c in completions]
        self.assertTrue(any("alpha" in p for p in paths))

    def test_at_with_space_after_at_returns_nothing(self):
        # "@foo bar" — space in prefix means we're past the mention word
        completions = self._completions("@alpha.py bar")
        self.assertEqual(completions, [])

    def test_at_limits_to_20_results(self):
        many_files = [f"zfile{i:02d}.py" for i in range(25)]
        with patch("iclaw.completer._get_git_files", return_value=many_files):
            completions = self._completions("@zfile")
        self.assertLessEqual(len(completions), 20)

    def test_at_excludes_gitignored_files(self):
        # git ls-files naturally excludes ignored files; simulate this by
        # returning only non-ignored files from _get_git_files.
        clean_files = ["visible.py", "README.md"]
        with patch("iclaw.completer._get_git_files", return_value=clean_files):
            completions = self._completions("@")
        paths = [c.text for c in completions]
        self.assertNotIn("visible.pyc", paths)
        self.assertNotIn("__pycache__", paths)
        self.assertIn("visible.py", paths)

    # --- / command completion ---

    def test_slash_alone_returns_all_commands(self):
        completions = self._completions("/")
        texts = [c.text for c in completions]
        # "/" prefix only matches slash-prefixed commands, not ".exit"
        for cmd in ["/provider_model", "/model", "/provider_search", "/copy", "/help"]:
            self.assertIn(cmd, texts)
        self.assertNotIn(".exit", texts)

    def test_slash_partial_filters_commands(self):
        completions = self._completions("/mod")
        texts = [c.text for c in completions]
        self.assertIn("/model", texts)
        self.assertNotIn("/provider_model", texts)
        self.assertNotIn("/copy", texts)
        self.assertNotIn("/help", texts)

    def test_dot_exit_completion(self):
        completions = self._completions(".")
        texts = [c.text for c in completions]
        self.assertIn(".exit", texts)

    def test_no_trigger_returns_nothing(self):
        completions = self._completions("hello world")
        self.assertEqual(completions, [])

    def test_at_takes_priority_over_slash_in_same_input(self):
        # Input has both / at start and @ later — @ should win
        completions = self._completions("/help @alph")
        paths = [c.text for c in completions]
        self.assertTrue(any("alpha" in p for p in paths))


if __name__ == "__main__":
    unittest.main()
