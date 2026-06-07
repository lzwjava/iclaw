import os
import unittest
from unittest.mock import MagicMock, patch

from iclaw import main


def _mock_session(*inputs):
    """Return a PromptSession mock whose .prompt_async() yields inputs in order."""

    session = MagicMock()

    async def _async_side_effect(*args, **kwargs):
        val = inputs_side_effect.pop(0)
        if isinstance(val, BaseException):
            raise val
        return val

    inputs_side_effect = list(inputs)
    session.prompt_async = MagicMock(side_effect=_async_side_effect)
    # Keep .prompt() too in case anything still references it
    session.prompt.side_effect = list(inputs)
    return session


def _ps(*inputs):
    """Patch target helper: returns PromptSession constructor mock."""
    m = MagicMock()
    m.return_value = _mock_session(*inputs)
    return m


class TestMain(unittest.TestCase):
    @patch("iclaw.main.http")
    @patch("iclaw.main.chat")
    @patch("iclaw.main.load_github_token")
    @patch("iclaw.main.PromptSession")
    def test_main_cli(self, mock_ps, mock_load, mock_chat, mock_http):
        mock_load.return_value = "gt"
        mock_ps.return_value = _mock_session(".exit")
        with (
            patch("sys.stdout"),
            patch("iclaw.main.get_copilot_token"),
            patch("iclaw.main.time.monotonic", return_value=0),
        ):
            main.main()

    def test_load_github_token(self):
        with patch("iclaw.config.CONFIG_PATH") as mp:
            mp.exists.return_value = True
            mp.read_text.return_value = '{"github_token": "t"}'
            self.assertEqual(main.load_github_token(), "t")

    def test_load_github_token_no_config(self):
        with patch("iclaw.config.CONFIG_PATH") as mp:
            mp.exists.return_value = False
            self.assertIsNone(main.load_github_token())

    def test_load_github_token_invalid_yaml(self):
        with patch("iclaw.config.CONFIG_PATH") as mp:
            mp.exists.return_value = True
            mp.read_text.return_value = "not yaml: [invalid"
            self.assertIsNone(main.load_github_token())

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value=None)
    @patch("iclaw.main.PromptSession")
    def test_main_no_token(self, mock_ps, mock_load, mock_http):
        mock_ps.return_value = _mock_session(".exit")
        with patch("sys.stdout"), patch("sys.stderr"):
            main.main()

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value="gt")
    @patch("iclaw.main.get_copilot_token", side_effect=Exception("fail"))
    @patch("iclaw.main.PromptSession")
    def test_main_copilot_token_error(self, mock_ps, mock_cp, mock_load, mock_http):
        mock_ps.return_value = _mock_session(".exit")
        with patch("sys.stdout"), patch("sys.stderr"):
            main.main()

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value="gt")
    @patch("iclaw.main.get_copilot_token", return_value="ct")
    @patch("iclaw.main.PromptSession")
    def test_main_empty_and_help(self, mock_ps, mock_cp, mock_load, mock_http):
        mock_ps.return_value = _mock_session("", "/help", "/", ".exit")
        with patch("sys.stdout"), patch("iclaw.main.time.monotonic", return_value=0):
            main.main()

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value="gt")
    @patch("iclaw.main.get_copilot_token", return_value="ct")
    @patch("iclaw.main.PromptSession")
    def test_main_eof(self, mock_ps, mock_cp, mock_load, mock_http):
        mock_ps.return_value = _mock_session(EOFError())
        with patch("sys.stdout"), patch("iclaw.main.time.monotonic", return_value=0):
            main.main()

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value=None)
    @patch("iclaw.main.PromptSession")
    def test_main_not_authenticated(self, mock_ps, mock_load, mock_http):
        mock_ps.return_value = _mock_session("hello", ".exit")
        with patch("sys.stdout"), patch("sys.stderr"):
            main.main()

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value="gt")
    @patch("iclaw.main.get_copilot_token", return_value="ct")
    @patch("iclaw.main.handle_copy_command")
    @patch("iclaw.main.PromptSession")
    def test_main_copy(self, mock_ps, mock_copy, mock_cp, mock_load, mock_http):
        mock_ps.return_value = _mock_session("/copy", ".exit")
        with patch("sys.stdout"), patch("iclaw.main.time.monotonic", return_value=0):
            main.main()
        mock_copy.assert_called_once()

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value="gt")
    @patch("iclaw.main.get_copilot_token", return_value="ct")
    @patch("iclaw.main.handle_model_provider_command", return_value=("copilot", None))
    @patch("iclaw.main.PromptSession")
    def test_main_model_provider(self, mock_ps, mock_mp, mock_cp, mock_load, mock_http):
        mock_ps.return_value = _mock_session("/provider_model", ".exit")
        with patch("sys.stdout"), patch("iclaw.main.time.monotonic", return_value=0):
            main.main()

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value="gt")
    @patch("iclaw.main.get_copilot_token", return_value="ct")
    @patch("iclaw.main.handle_model_command", return_value="gpt-4o")
    @patch("iclaw.main.PromptSession")
    def test_main_model(self, mock_ps, mock_mc, mock_cp, mock_load, mock_http):
        mock_ps.return_value = _mock_session("/model", ".exit")
        with patch("sys.stdout"), patch("iclaw.main.time.monotonic", return_value=0):
            main.main()

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value="gt")
    @patch("iclaw.main.get_copilot_token", return_value="ct")
    @patch("iclaw.main.handle_search_provider_command", return_value="bing")
    @patch("iclaw.main.PromptSession")
    def test_main_search_provider(
        self, mock_ps, mock_sp, mock_cp, mock_load, mock_http
    ):
        mock_ps.return_value = _mock_session("/provider_search", ".exit")
        with patch("sys.stdout"), patch("iclaw.main.time.monotonic", return_value=0):
            main.main()

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value="gt")
    @patch("iclaw.main.get_copilot_token", return_value="ct")
    @patch("iclaw.main.chat", return_value={"content": "Today is 2026-03-30."})
    @patch("iclaw.main.web_search", return_value="search results here")
    @patch("iclaw.main.PromptSession")
    def test_main_search_command(
        self, mock_ps, mock_ws, mock_chat, mock_cp, mock_load, mock_http
    ):
        mock_ps.return_value = _mock_session("/search what is today", ".exit")
        with patch("sys.stdout"), patch("iclaw.main.time.monotonic", return_value=0):
            main.main()
        mock_ws.assert_called_once_with(
            "what is today", num_results=5, provider="duckduckgo"
        )

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value="gt")
    @patch("iclaw.main.get_copilot_token", return_value="ct")
    @patch("iclaw.main.chat", return_value={"content": "hi"})
    @patch("iclaw.main.PromptSession")
    def test_main_chat(self, mock_ps, mock_chat, mock_cp, mock_load, mock_http):
        mock_ps.return_value = _mock_session("hello", ".exit")
        with patch("sys.stdout"), patch("iclaw.main.time.monotonic", return_value=0):
            main.main()

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value="gt")
    @patch("iclaw.main.get_copilot_token", return_value="ct")
    @patch("iclaw.main.chat", side_effect=Exception("API error"))
    @patch("iclaw.main.PromptSession")
    def test_main_chat_error(self, mock_ps, mock_chat, mock_cp, mock_load, mock_http):
        mock_ps.return_value = _mock_session("hello", ".exit")
        with (
            patch("sys.stdout"),
            patch("sys.stderr"),
            patch("iclaw.main.time.monotonic", return_value=0),
        ):
            main.main()

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value="gt")
    @patch("iclaw.main.get_copilot_token", return_value="ct")
    @patch("iclaw.main.chat")
    @patch("iclaw.main.web_search", return_value="search results")
    @patch("iclaw.main.PromptSession")
    def test_main_tool_call_web_search(
        self, mock_ps, mock_ws, mock_chat, mock_cp, mock_load, mock_http
    ):
        mock_ps.return_value = _mock_session("hello", ".exit")
        mock_chat.side_effect = [
            {
                "content": None,
                "tool_calls": [
                    {
                        "id": "tc1",
                        "function": {
                            "name": "web_search",
                            "arguments": '{"query": "test"}',
                        },
                    }
                ],
            },
            {"content": "answer"},
        ]
        with patch("sys.stdout"), patch("iclaw.main.time.monotonic", return_value=0):
            main.main()
        mock_ws.assert_called_once()

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value="gt")
    @patch("iclaw.main.get_copilot_token", return_value="ct")
    @patch("iclaw.main.chat")
    @patch("iclaw.main.exec", return_value="output")
    @patch("iclaw.main.PromptSession")
    def test_main_tool_call_exec(
        self, mock_ps, mock_exec, mock_chat, mock_cp, mock_load, mock_http
    ):
        mock_ps.return_value = _mock_session("hello", ".exit")
        mock_chat.side_effect = [
            {
                "content": None,
                "tool_calls": [
                    {
                        "id": "tc1",
                        "function": {
                            "name": "exec",
                            "arguments": '{"command": "echo hi"}',
                        },
                    }
                ],
            },
            {"content": "done"},
        ]
        with patch("sys.stdout"), patch("iclaw.main.time.monotonic", return_value=0):
            main.main()

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value="gt")
    @patch("iclaw.main.get_copilot_token", return_value="ct")
    @patch("iclaw.main.chat")
    @patch("iclaw.main.PromptSession")
    def test_main_tool_call_edit(
        self, mock_ps, mock_chat, mock_cp, mock_load, mock_http
    ):
        mock_ps.return_value = _mock_session("hello", ".exit")
        mock_chat.side_effect = [
            {
                "content": None,
                "tool_calls": [
                    {
                        "id": "tc1",
                        "function": {
                            "name": "edit",
                            "arguments": '{"file_path": "/tmp/test_edit_main.txt", "edit_content": "--- a\\n+++ b\\n@@ -1,1 +1,1 @@\\n-old\\n+new"}',
                        },
                    }
                ],
            },
            {"content": "edited"},
        ]
        tmp = "/tmp/test_edit_main.txt"
        with open(tmp, "w") as f:
            f.write("old\n")
        try:
            with (
                patch("sys.stdout"),
                patch("iclaw.main.time.monotonic", return_value=0),
            ):
                main.main()
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value="gt")
    @patch("iclaw.main.get_copilot_token", return_value="ct")
    @patch("iclaw.main.chat", return_value={"content": "hi"})
    @patch("iclaw.main.PromptSession")
    def test_main_token_refresh(
        self, mock_ps, mock_chat, mock_cp, mock_load, mock_http
    ):
        mock_ps.return_value = _mock_session("hello", ".exit")
        # asyncio.run() calls time.monotonic() internally (shutdown_asyncgens
        # etc.), and since patch("iclaw.main.time.monotonic") patches the real
        # time.monotonic globally, those internal calls consume side_effect
        # entries too.  Use a callable that tracks call count so we can
        # control exactly which value the application code sees.
        #
        # We need: startup monotonic() returns a low value T so that
        #   token_expiry = T + TOKEN_REFRESH_INTERVAL
        # and later monotonic() returns a value >= token_expiry to trigger
        # refresh.  asyncio internals may consume 0-2 calls before the app
        # code runs.
        call_count = {"n": 0}

        def _monotonic():
            call_count["n"] += 1
            # First few calls may be asyncio internals; return 0 for them
            # and for the startup call.  Once we've had at least 2 calls
            # (startup done), switch to 99999 so the expiry check triggers.
            if call_count["n"] <= 2:
                return 0
            return 99999

        with (
            patch("sys.stdout"),
            patch("iclaw.main.time.monotonic", side_effect=_monotonic),
        ):
            main.main()
        # get_copilot_token called twice: once at startup, once on refresh
        self.assertEqual(mock_cp.call_count, 2)

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value="gt")
    @patch("iclaw.main.get_copilot_token", return_value="ct")
    @patch(
        "iclaw.main.handle_model_provider_command",
        return_value=("copilot", "new_token"),
    )
    @patch("iclaw.main.PromptSession")
    def test_main_model_provider_with_token(
        self, mock_ps, mock_mp, mock_cp, mock_load, mock_http
    ):
        mock_ps.return_value = _mock_session("/provider_model", ".exit")
        with patch("sys.stdout"), patch("iclaw.main.time.monotonic", return_value=0):
            main.main()

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value="gt")
    @patch("iclaw.main.get_copilot_token", return_value="ct")
    @patch("iclaw.main.PromptSession")
    def test_main_status(self, mock_ps, mock_cp, mock_load, mock_http):
        mock_ps.return_value = _mock_session("/status", ".exit")
        with patch("sys.stdout"), patch("iclaw.main.time.monotonic", return_value=0):
            main.main()

    @patch("iclaw.main.http")
    @patch("iclaw.main.load_github_token", return_value="gt")
    @patch("iclaw.main.get_copilot_token", return_value="ct")
    @patch("iclaw.main.PromptSession")
    def test_main_log(self, mock_ps, mock_cp, mock_load, mock_http):
        mock_ps.return_value = _mock_session(
            "/log", "/log info", "/log verbose", ".exit"
        )
        with patch("sys.stdout"), patch("iclaw.main.time.monotonic", return_value=0):
            main.main()


if __name__ == "__main__":
    unittest.main()
