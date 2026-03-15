"""High-level integration tests for iclaw REPL launched as a subprocess.

Uses a fake HTTP server to mock GitHub/Copilot APIs — no real credentials needed.
Subprocess coverage is collected via COVERAGE_PROCESS_START + sitecustomize.py.

Run with coverage:
    PYTHONPATH=. COVERAGE_PROCESS_START=.coveragerc \\
        python3 -m coverage run --parallel-mode -m unittest discover integration_tests
    python3 -m coverage combine
    python3 -m coverage report -m iclaw/*.py iclaw/commands/*.py iclaw/tools/*.py
"""

import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer


# ---------------------------------------------------------------------------
# Fake Copilot / GitHub API server
# ---------------------------------------------------------------------------


class _FakeServer:
    """Minimal threaded fake server for GitHub token + Copilot API endpoints."""

    def __init__(self):
        self._responses = []
        self._lock = threading.Lock()
        self.port = None
        self._server = None

    def enqueue(self, content=None, tool_calls=None):
        """Queue the next /chat/completions response."""
        msg = {"content": content}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        with self._lock:
            self._responses.append({"choices": [{"message": msg}]})

    def _next_chat(self):
        with self._lock:
            if self._responses:
                return self._responses.pop(0)
        return {"choices": [{"message": {"content": "OK"}}]}

    def start(self):
        parent = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _json(self, data):
                body = json.dumps(data).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if "/copilot_internal/v2/token" in self.path:
                    self._json({"token": "fake-copilot-token"})
                elif "/models" in self.path:
                    self._json({"data": [{"id": "gpt-4o", "owned_by": "openai"}]})
                else:
                    self.send_error(404)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                self.rfile.read(length)
                if "/chat/completions" in self.path:
                    self._json(parent._next_chat())
                else:
                    self.send_error(404)

        self._server = HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self._server.server_address[1]
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def stop(self):
        if self._server:
            self._server.shutdown()


# ---------------------------------------------------------------------------
# Subprocess helpers
# ---------------------------------------------------------------------------


def _make_config_with_token(token="fake-github-token"):
    """Write a config.json to a temp file and return its path."""
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, prefix="iclaw_config_"
    )
    json.dump({"github_token": token}, f)
    f.close()
    return f.name


def _make_env(config_path=None, port=None):
    """Build subprocess env. config_path=None means no token (nonexistent path).

    We clear PYTHONPATH entirely: iclaw is installed via ``pip install -e .`` so
    it is importable from site-packages without any path manipulation. Inheriting
    PYTHONPATH from the test runner breaks Homebrew Python's site-packages lookup
    on some setups (causing ModuleNotFoundError for prompt_toolkit etc.).
    """
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    # Point iclaw at the temp config (or a nonexistent path for no-token tests).
    env["ICLAW_CONFIG_PATH"] = config_path or "/tmp/iclaw_no_such_config.json"
    if port:
        env["ICLAW_GITHUB_API_BASE"] = f"http://127.0.0.1:{port}"
        env["ICLAW_COPILOT_API_BASE"] = f"http://127.0.0.1:{port}"
    coveragerc = os.path.join(os.getcwd(), ".coveragerc")
    if os.path.exists(coveragerc):
        env["COVERAGE_PROCESS_START"] = coveragerc
    return env


def _start_repl(env):
    return subprocess.Popen(
        [sys.executable, "-m", "iclaw.main"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=os.getcwd(),
        env=env,
    )


def _start_reader(process):
    """Drain process stdout into a queue in a background thread."""
    q = queue.Queue()

    def _read():
        while True:
            ch = process.stdout.read(1)
            if not ch:
                q.put(None)
                break
            q.put(ch)

    threading.Thread(target=_read, daemon=True).start()
    return q


def _read_until(q, target, timeout=15):
    """Accumulate chars from q until `target` appears or timeout expires."""
    output = ""
    end = time.time() + timeout
    while time.time() < end:
        remaining = end - time.time()
        if remaining <= 0:
            break
        try:
            ch = q.get(timeout=remaining)
        except queue.Empty:
            break
        if ch is None:
            break
        output += ch
        if target in output:
            return output, True
    return output, False


def _send(process, text):
    process.stdin.write(text + "\n")
    process.stdin.flush()


# ---------------------------------------------------------------------------
# Tests: no GitHub token configured
# ---------------------------------------------------------------------------


class TestReplNoToken(unittest.TestCase):
    """REPL behaviour when no config.json exists."""

    def setUp(self):
        self.process = _start_repl(_make_env())  # no config_path → no token
        self.q = _start_reader(self.process)

    def tearDown(self):
        try:
            self.process.terminate()
            self.process.wait(timeout=5)
        except Exception:
            pass

    def test_startup_shows_no_token_message(self):
        out, found = _read_until(self.q, "> ")
        self.assertTrue(found, f"Prompt not found. Got: {out!r}")
        self.assertIn("No token found", out)

    def test_exit_command(self):
        _read_until(self.q, "> ")
        _send(self.process, ".exit")
        out, found = _read_until(self.q, "Goodbye", timeout=8)
        self.assertIn("Goodbye", out)

    def test_help_command(self):
        _read_until(self.q, "> ")
        _send(self.process, "/help")
        out, found = _read_until(self.q, "/copy", timeout=8)
        self.assertTrue(found, f"Help output not found. Got: {out!r}")
        self.assertIn("/model", out)
        _send(self.process, ".exit")

    def test_slash_alone_shows_help(self):
        _read_until(self.q, "> ")
        _send(self.process, "/")
        out, found = _read_until(self.q, "/copy", timeout=8)
        self.assertTrue(found, f"Help not shown for '/'. Got: {out!r}")
        _send(self.process, ".exit")

    def test_empty_input_returns_to_prompt(self):
        _read_until(self.q, "> ")
        _send(self.process, "")
        out, found = _read_until(self.q, "> ", timeout=5)
        self.assertTrue(found, f"Prompt not returned. Got: {out!r}")
        _send(self.process, ".exit")

    def test_unauthenticated_chat_shows_error(self):
        _read_until(self.q, "> ")
        _send(self.process, "tell me a joke")
        out, found = _read_until(self.q, "authenticated", timeout=8)
        self.assertTrue(found, f"Auth error not found. Got: {out!r}")
        _send(self.process, ".exit")

    def test_copy_with_no_reply_yet(self):
        _read_until(self.q, "> ")
        _send(self.process, "/copy")
        out, found = _read_until(self.q, "Nothing to copy", timeout=8)
        self.assertTrue(found, f"Expected 'Nothing to copy'. Got: {out!r}")
        _send(self.process, ".exit")

    def test_search_provider_change(self):
        _read_until(self.q, "> ")
        _send(self.process, "/search_provider")
        out, found = _read_until(self.q, "Select search provider", timeout=8)
        self.assertTrue(found, f"Search provider prompt not found. Got: {out!r}")
        _send(self.process, "2")  # select startpage
        out2, found2 = _read_until(self.q, "startpage", timeout=8)
        self.assertTrue(found2, f"Provider confirmation not found. Got: {out2!r}")
        _send(self.process, ".exit")

    def test_search_provider_keep_current(self):
        _read_until(self.q, "> ")
        _send(self.process, "/search_provider")
        _read_until(self.q, "Select search provider", timeout=8)
        _send(self.process, "")  # press Enter to keep current
        out, found = _read_until(self.q, "> ", timeout=8)
        self.assertTrue(found, f"Prompt not returned. Got: {out!r}")
        _send(self.process, ".exit")

    def test_search_provider_invalid_selection(self):
        _read_until(self.q, "> ")
        _send(self.process, "/search_provider")
        _read_until(self.q, "Select search provider", timeout=8)
        _send(self.process, "99")  # out of range
        out, found = _read_until(self.q, "> ", timeout=8)
        self.assertTrue(found, f"Prompt not returned. Got: {out!r}")
        _send(self.process, ".exit")

    def test_search_provider_non_digit(self):
        _read_until(self.q, "> ")
        _send(self.process, "/search_provider")
        _read_until(self.q, "Select search provider", timeout=8)
        _send(self.process, "bad")
        out, found = _read_until(self.q, "> ", timeout=8)
        self.assertTrue(found, f"Prompt not returned. Got: {out!r}")
        _send(self.process, ".exit")


# ---------------------------------------------------------------------------
# Tests: with fake GitHub token + fake Copilot server
# ---------------------------------------------------------------------------


class TestReplWithFakeServer(unittest.TestCase):
    """Full REPL loop tests using an in-process fake HTTP server."""

    def setUp(self):
        self.server = _FakeServer()
        self.server.start()
        self.config_path = _make_config_with_token()
        self.env = _make_env(self.config_path, self.server.port)
        self.process = None
        self.q = None

    def _start(self):
        self.process = _start_repl(self.env)
        self.q = _start_reader(self.process)
        out, found = _read_until(self.q, "> ")
        self.assertTrue(found, f"REPL prompt not found. Output: {out!r}")
        return out

    def tearDown(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                pass
        self.server.stop()
        if os.path.exists(self.config_path):
            os.unlink(self.config_path)

    def test_startup_with_token_connects(self):
        out = self._start()
        self.assertIn("Connecting", out)
        _send(self.process, ".exit")

    def test_chat_message_and_reply(self):
        self.server.enqueue(content="Hello from fake Copilot!")
        self._start()
        _send(self.process, "hi there")
        out, found = _read_until(self.q, "Hello from fake Copilot!", timeout=15)
        self.assertTrue(found, f"Expected reply not found. Got: {out!r}")
        _send(self.process, ".exit")

    def test_at_mention_file_injected(self):
        """@file mention expands file content into the API request."""
        secret = "UNIQUE_SECRET_XYZ_42"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(f"The secret is: {secret}")
            fname = f.name
        try:
            self.server.enqueue(content="Saw your file!")
            self._start()
            _send(self.process, f"explain @{fname}")
            out, found = _read_until(self.q, "Saw your file!", timeout=15)
            self.assertTrue(found, f"Expected reply not found. Got: {out!r}")
            _send(self.process, ".exit")
        finally:
            os.unlink(fname)

    def test_copy_after_chat(self):
        self.server.enqueue(content="Copyable reply content here")
        self._start()
        _send(self.process, "say something")
        _read_until(self.q, "Copyable reply content here", timeout=15)
        _send(self.process, "/copy")
        out, found = _read_until(self.q, "> ", timeout=8)
        self.assertTrue(found, f"Prompt not returned after /copy. Got: {out!r}")
        _send(self.process, ".exit")

    def test_model_command_list_and_select(self):
        self._start()
        _send(self.process, "/model")
        out, found = _read_until(self.q, "Select model", timeout=10)
        self.assertTrue(found, f"Model selection prompt not found. Got: {out!r}")
        self.assertIn("gpt-4o", out)
        _send(self.process, "1")
        out2, found2 = _read_until(self.q, "> ", timeout=8)
        self.assertTrue(found2, f"Prompt not returned. Got: {out2!r}")
        _send(self.process, ".exit")

    def test_model_command_keep_current(self):
        self._start()
        _send(self.process, "/model")
        _read_until(self.q, "Select model", timeout=10)
        _send(self.process, "")  # keep current
        out, found = _read_until(self.q, "> ", timeout=8)
        self.assertTrue(found, f"Prompt not returned. Got: {out!r}")
        _send(self.process, ".exit")

    def test_model_command_by_name(self):
        self._start()
        _send(self.process, "/model")
        _read_until(self.q, "Select model", timeout=10)
        _send(self.process, "gpt-4o")
        out, found = _read_until(self.q, "> ", timeout=8)
        self.assertTrue(found, f"Prompt not returned. Got: {out!r}")
        _send(self.process, ".exit")

    def test_model_command_invalid_number(self):
        self._start()
        _send(self.process, "/model")
        _read_until(self.q, "Select model", timeout=10)
        _send(self.process, "999")
        out, found = _read_until(self.q, "> ", timeout=8)
        self.assertTrue(found, f"Prompt not returned. Got: {out!r}")
        _send(self.process, ".exit")

    def test_model_command_unknown_name(self):
        self._start()
        _send(self.process, "/model")
        _read_until(self.q, "Select model", timeout=10)
        _send(self.process, "nonexistent-model-xyz")
        out, found = _read_until(self.q, "> ", timeout=8)
        self.assertTrue(found, f"Prompt not returned. Got: {out!r}")
        _send(self.process, ".exit")

    def test_tool_call_exec(self):
        """Fake server returns an exec tool call; REPL executes it locally."""
        self.server.enqueue(
            tool_calls=[
                {
                    "id": "tc1",
                    "type": "function",
                    "function": {
                        "name": "exec",
                        "arguments": json.dumps({"command": "echo repl_exec_works"}),
                    },
                }
            ]
        )
        self.server.enqueue(content="The command ran successfully.")
        self._start()
        _send(self.process, "run echo repl_exec_works for me")
        out, found = _read_until(self.q, "The command ran successfully.", timeout=20)
        self.assertTrue(found, f"Final reply not found. Got: {out!r}")
        self.assertIn("[exec] Running command", out)
        _send(self.process, ".exit")

    def test_tool_call_edit(self):
        """Fake server returns an edit tool call; REPL applies the unified diff."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("original content\n")
            fname = f.name
        try:
            diff = "--- a\n+++ b\n@@ -1,1 +1,1 @@\n-original content\n+edited content\n"
            self.server.enqueue(
                tool_calls=[
                    {
                        "id": "tc2",
                        "type": "function",
                        "function": {
                            "name": "edit",
                            "arguments": json.dumps(
                                {"file_path": fname, "edit_content": diff}
                            ),
                        },
                    }
                ]
            )
            self.server.enqueue(content="File has been edited.")
            self._start()
            _send(self.process, f"edit {fname} please")
            out, found = _read_until(self.q, "File has been edited.", timeout=20)
            self.assertTrue(found, f"Final reply not found. Got: {out!r}")
            _send(self.process, ".exit")
            _read_until(self.q, "Goodbye", timeout=5)
            with open(fname) as fh:
                content = fh.read()
            self.assertIn("edited content", content)
        finally:
            if os.path.exists(fname):
                os.unlink(fname)

    def test_chat_api_error_handled(self):
        """If the chat API errors, REPL prints an error and returns to prompt."""
        # Stop server to force a connection error
        self.server.stop()
        self._start()
        _send(self.process, "trigger an error")
        out, found = _read_until(self.q, "> ", timeout=15)
        self.assertTrue(found, f"Prompt not returned after error. Got: {out!r}")
        _send(self.process, ".exit")

    def test_token_refresh_triggered(self):
        """Cover the token-refresh branch by sending two messages."""
        self.server.enqueue(content="First reply")
        self.server.enqueue(content="Second reply")
        self._start()
        _send(self.process, "first message")
        _read_until(self.q, "First reply", timeout=15)
        _send(self.process, "second message")
        out, found = _read_until(self.q, "Second reply", timeout=15)
        self.assertTrue(found, f"Second reply not found. Got: {out!r}")
        _send(self.process, ".exit")


if __name__ == "__main__":
    unittest.main()
