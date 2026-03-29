# /log Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/log` command with `verbose`/`info` levels to control REPL output verbosity.

**Architecture:** Central `log.py` module with `log_info()`/`log_verbose()` functions. All `print()` calls in tool modules replaced with these. Level persisted to config.json.

**Tech Stack:** Python 3, unittest, prompt_toolkit (existing)

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `iclaw/log.py` | Create | Log level state, `log_info()`, `log_verbose()` |
| `iclaw/commands/log.py` | Create | `/log` command handler |
| `tests/test_log.py` | Create | Tests for log module |
| `tests/test_log_command.py` | Create | Tests for /log command handler |
| `iclaw/config.py` | Modify | Add `log_level` to load/save |
| `iclaw/completer.py` | Modify | Add `/log` to COMMANDS |
| `iclaw/web_search.py` | Modify | Replace `print()` with log calls |
| `iclaw/exec_tool.py` | Modify | Replace `print()` with log call |
| `iclaw/main.py` | Modify | Dispatch `/log`, add tool call logging, update `/status` and COMMANDS_HELP |

---

### Task 1: Create `iclaw/log.py` with tests

**Files:**
- Create: `iclaw/log.py`
- Create: `tests/test_log.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_log.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=. python3 -m unittest tests/test_log.py -v`
Expected: ImportError — `iclaw.log` does not exist yet

- [ ] **Step 3: Implement `iclaw/log.py`**

```python
# iclaw/log.py
INFO = 0
VERBOSE = 1

_level = VERBOSE


def set_level(level):
    global _level
    _level = level


def get_level():
    return _level


def log_info(message):
    print(message)


def log_verbose(message):
    if _level >= VERBOSE:
        print(message)


def level_name(level):
    if level == INFO:
        return "info"
    else:
        return "verbose"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=. python3 -m unittest tests/test_log.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add iclaw/log.py tests/test_log.py
git commit -m "feat(log): add log module with info/verbose levels"
```

---

### Task 2: Create `/log` command handler with tests

**Files:**
- Create: `iclaw/commands/log.py`
- Create: `tests/test_log_command.py`
- Modify: `iclaw/config.py:28-48` — add `log_level` to load/save
- Modify: `tests/test_config.py` — update existing tests for new parameter

- [ ] **Step 1: Write failing tests for the command handler**

```python
# tests/test_log_command.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=. python3 -m unittest tests/test_log_command.py -v`
Expected: ImportError — `iclaw.commands.log` does not exist yet

- [ ] **Step 3: Implement `iclaw/commands/log.py`**

```python
# iclaw/commands/log.py
from iclaw import log

LEVELS = {"verbose": log.VERBOSE, "info": log.INFO}


def handle_log_command(arg):
    if arg is None:
        print(f"Log level: {log.level_name(log.get_level())}")
        return

    if arg not in LEVELS:
        print(f"Unknown log level: {arg}. Use 'verbose' or 'info'.")
        return

    log.set_level(LEVELS[arg])
    print(f"Log level set to: {arg}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=. python3 -m unittest tests/test_log_command.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Update `iclaw/config.py` — add `log_level` to load/save**

In `load_session_settings()`, add to the returned dict:
```python
"log_level": config.get("log_level", "verbose"),
```

In `save_session_settings()`, add `log_level="verbose"` to the keyword parameters and add this line in the body:
```python
config["log_level"] = log_level
```

- [ ] **Step 6: Update `tests/test_config.py` — add `log_level` to existing `save_session_settings` calls**

Every existing call to `save_session_settings(...)` in the test file needs `log_level="verbose"` added. There are 2 calls (lines 35 and 52). Also add a test for loading log_level:

```python
def test_load_log_level_default(self):
    with patch("iclaw.config.CONFIG_PATH") as mp:
        mp.exists.return_value = True
        mp.read_text.return_value = json.dumps({})
        settings = load_session_settings()
    self.assertEqual(settings["log_level"], "verbose")

def test_load_log_level_set(self):
    with patch("iclaw.config.CONFIG_PATH") as mp:
        mp.exists.return_value = True
        mp.read_text.return_value = json.dumps({"log_level": "info"})
        settings = load_session_settings()
    self.assertEqual(settings["log_level"], "info")
```

- [ ] **Step 7: Run all tests**

Run: `PYTHONPATH=. python3 -m unittest tests/test_log_command.py tests/test_config.py -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add iclaw/commands/log.py tests/test_log_command.py iclaw/config.py tests/test_config.py
git commit -m "feat(log): add /log command handler and config persistence"
```

---

### Task 3: Wire `/log` into REPL and update completer

**Files:**
- Modify: `iclaw/main.py:29-40` — add to COMMANDS_HELP
- Modify: `iclaw/main.py:48-54` — load log_level from settings, init log module
- Modify: `iclaw/main.py:74-190` — add `/log` command dispatch
- Modify: `iclaw/main.py:182-190` — add log_level to `/status` output
- Modify: `iclaw/completer.py:6-17` — add `/log` to COMMANDS

- [ ] **Step 1: Add `/log` to `COMMANDS` in `iclaw/completer.py`**

Add `"/log"` to the COMMANDS list (after `/ca_bundle`).

- [ ] **Step 2: Add `/log` to `COMMANDS_HELP` in `iclaw/main.py`**

Add this tuple after the `/ca_bundle` entry:
```python
("/log", "Set log verbosity (usage: /log [verbose|info])"),
```

- [ ] **Step 3: Add import and init in `iclaw/main.py`**

Add imports at top:
```python
from iclaw import log
from iclaw.commands.log import handle_log_command
```

After `settings = load_session_settings()` (line 48), after the existing settings extraction, add:
```python
log_level = settings["log_level"]
log.set_level({"info": log.INFO, "verbose": log.VERBOSE}.get(log_level, log.VERBOSE))
```

- [ ] **Step 4: Add `/log` command dispatch in the REPL loop**

Add before the `/status` handler (around line 182):
```python
if user_input == "/log" or user_input.startswith("/log "):
    parts = user_input.split(maxsplit=1)
    arg = parts[1] if len(parts) > 1 else None
    handle_log_command(arg)
    if arg in ("verbose", "info"):
        log_level = arg
        save_session_settings(
            model_provider=model_provider,
            current_model=current_model,
            search_provider=search_provider,
            proxy=proxy,
            ca_bundle=ca_bundle,
            log_level=log_level,
        )
    continue
```

- [ ] **Step 5: Add log_level to `/status` output**

In the `/status` handler, add after the `ca_bundle` line:
```python
print(f"  log_level:       {log_level}")
```

- [ ] **Step 6: Add `log_level=log_level` to ALL existing `save_session_settings()` calls in `main.py`**

There are 5 existing calls (lines 102, 112, 148, 161, 174). Each needs `log_level=log_level` added.

- [ ] **Step 7: Add `/log` dispatch test in `tests/test_main.py`**

Add this test following the same pattern as `test_main_status`:

```python
@patch("iclaw.main.http")
@patch("iclaw.main.load_github_token", return_value="gt")
@patch("iclaw.main.get_copilot_token", return_value="ct")
@patch("iclaw.main.PromptSession")
def test_main_log(self, mock_ps, mock_cp, mock_load, mock_http):
    mock_ps.return_value = _mock_session("/log", "/log info", "/log verbose", ".exit")
    with patch("sys.stdout"), patch("iclaw.main.time.monotonic", return_value=0):
        main.main()
```

- [ ] **Step 8: Run existing tests to check nothing broke**

Run: `PYTHONPATH=. python3 -m unittest discover tests -v`
Expected: All PASS

- [ ] **Step 9: Commit**

```bash
git add iclaw/main.py iclaw/completer.py tests/test_main.py
git commit -m "feat(log): wire /log command into REPL with persistence"
```

---

### Task 4: Replace `print()` with log calls in tool modules

**Files:**
- Modify: `iclaw/web_search.py:25,60,98,203,226,232,262` — replace `print()` calls
- Modify: `iclaw/exec_tool.py:6` — replace `print()` call

- [ ] **Step 1: Update `iclaw/web_search.py`**

Add import at top:
```python
from iclaw.log import log_info, log_verbose
```

Replace these `print()` calls:
- Line 25: `print(f"[web search] Error searching DDG: {e}")` → `log_info(f"[web search] Error searching DDG: {e}")`
- Line 60: `print(f"[web search] Error searching Startpage: {e}")` → `log_info(f"[web search] Error searching Startpage: {e}")`
- Line 98: `print(f"[web search] Error searching Bing: {e}")` → `log_info(f"[web search] Error searching Bing: {e}")`
- Line 203: `print("[web search] Error: TAVILY_API_KEY not set.")` → `log_info("[web search] Error: TAVILY_API_KEY not set.")`
- Line 226: `print(f"[web search] Error searching Tavily: {e}")` → `log_info(f"[web search] Error searching Tavily: {e}")`
- Line 232: `print(f"[web search] Searching ({provider}): {query}")` → `log_verbose(f"[web search] Searching ({provider}): {query}")`
- Line 262: `print(f"[web search] Fetched: {info['url']}")` → `log_verbose(f"[web search] Fetched: {info['url']}")`

- [ ] **Step 2: Update `iclaw/exec_tool.py`**

Add import at top:
```python
from iclaw.log import log_verbose
```

Replace line 6: `print(f"[exec] Running command: {command}")` → `log_verbose(f"[exec] Running command: {command}")`

- [ ] **Step 3: Run tests to verify nothing broke**

Run: `PYTHONPATH=. python3 -m unittest discover tests -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add iclaw/web_search.py iclaw/exec_tool.py
git commit -m "refactor: replace print() with log_info/log_verbose in tool modules"
```

---

### Task 5: Add tool call input/output logging in `main.py`

**Files:**
- Modify: `iclaw/main.py:206-256` — add verbose logging around tool calls

- [ ] **Step 1: Add verbose logging in the tool call loop**

In the tool call loop (after `function_args = json.loads(...)` on line 210), add:
```python
log.log_verbose(f"[tool] Calling {function_name} with {json.dumps(function_args)}")
```

After each tool result is appended to messages (after lines 225, 236, 252), add:
```python
log.log_verbose(f"[tool] Result: {<result_content>}")
```

Where `<result_content>` is `search_context`, `output`, or the edit success message respectively.

- [ ] **Step 2: Replace remaining `print()` calls in `main.py` with log calls**

Replace final reply prints and startup messages:
- Line 57: `print("Connecting to GitHub Copilot...")` → `log.log_info("Connecting to GitHub Copilot...")`
- Line 64: `print("No token found...")` → `log.log_info("No token found. Type /provider_model to authenticate.\n")`
- Line 67-70: startup help messages → `log.log_info(...)`
- Line 124: `print(f"\n{search_context}\n")` → `log.log_info(f"\n{search_context}\n")`
- Line 142: `print(f"\n{reply}\n")` → `log.log_info(f"\n{reply}\n")`
- Line 261: `print(f"\n{reply}\n")` → `log.log_info(f"\n{reply}\n")`

Note: Keep `print()` for interactive prompts (help display, goodbye), error output to stderr, and command handler outputs (those are already `log_info` level by nature as direct user feedback).

- [ ] **Step 3: Run all tests**

Run: `PYTHONPATH=. python3 -m unittest discover tests -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add iclaw/main.py
git commit -m "feat(log): add tool call input/output verbose logging"
```

---

### Task 6: Final verification

- [ ] **Step 1: Run full test suite**

Run: `PYTHONPATH=. python3 -m unittest discover tests -v`
Expected: All PASS

- [ ] **Step 2: Run linter and formatter**

Run: `ruff check . && ruff format --check .`
Expected: No errors

- [ ] **Step 3: Manual smoke test**

Start `iclaw` and verify:
1. `/log` shows "Log level: verbose"
2. `/log info` sets level, `/status` shows `log_level: info`
3. `/log verbose` restores verbose
4. `/log garbage` shows error message
5. `/help` shows `/log` command
6. Restart iclaw — level persists from config
