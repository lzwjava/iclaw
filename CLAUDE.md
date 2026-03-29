# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -e .                    # Install package in editable mode
iclaw-login                         # Authenticate via GitHub device flow
iclaw                               # Start the interactive CLI REPL
ruff check .                        # Lint
ruff format .                       # Format (also runs on pre-commit)
```

### Running Tests

```bash
# Unit tests (no credentials needed)
export PYTHONPATH=$PYTHONPATH:.
python3 -m unittest discover tests

# Single test file
python3 -m unittest tests/test_main.py

# Single test case
python3 -m unittest tests/test_main.py::TestMain::test_main_chat

# With coverage
pip install coverage
python3 -m coverage run -m unittest discover tests
python3 -m coverage report -m iclaw/*.py iclaw/commands/*.py iclaw/tools/*.py

# Integration tests (require GITHUB_TOKEN_INTEGRATION env var)
GITHUB_TOKEN_INTEGRATION=<token> python3 -m unittest discover integration_tests
```

### GitHub Actions

- **`.github/workflows/test.yaml`** — Runs on push/PR touching `iclaw/**` or `tests/**`. Runs unit tests with `coverage` against `iclaw/*.py`, `iclaw/commands/*.py`, `iclaw/tools/*.py`.
- **`.github/workflows/integration.yaml`** — Runs on push/PR touching `mini_copilot/**` or `integration_tests/**`. Skips silently if `GITHUB_TOKEN_INTEGRATION` secret is not set.

## Architecture

**Authentication flow:**
1. `iclaw-login` runs GitHub OAuth Device Flow → saves `github_token` to `~/.config/iclaw/config.json`
2. `iclaw` startup reads the token via `iclaw/config.py:load_github_token()`, then exchanges it for a short-lived Copilot token (`iclaw/github_api.py:get_copilot_token()`)
3. The Copilot token is refreshed every `TOKEN_REFRESH_INTERVAL` seconds (24 min) during the session

**REPL loop (`iclaw/main.py:main()`):**
- Uses `prompt_toolkit.PromptSession` with `IclawCompleter` for tab-completion
- Commands (`/model`, `/copy`, etc.) are handled before messages reach the API
- User input passes through `resolve_at_mentions()` to expand `@filepath` references into `<file>` XML tags prepended to the message
- Calls `github_api.chat()` with the full message history and `TOOLS`
- Handles agentic tool-call loops: the model may return `tool_calls` for `web_search`, `exec`, or `edit`; results are appended as `role: tool` messages and the API is called again until a plain text reply is returned

**Tool definitions (`iclaw/tools/defs.py`):**
- `web_search` — delegates to `iclaw/web_search.py` (DuckDuckGo or Tavily based on `search_provider`)
- `exec` — delegates to `iclaw/exec_tool.py` (runs shell commands locally)
- `edit` — delegates to `iclaw/tools/edit_tool.py` (applies unified diffs to files)

**Key modules:**
- `iclaw/completer.py` — `IclawCompleter`: `@`-mention file completion (via `git ls-files`) and `/`-command completion
- `iclaw/at_mention.py` — `resolve_at_mentions()`: expands `@path` tokens into file content XML
- `iclaw/github_api.py` — `get_copilot_token()`, `get_models()`, `chat()`
- `iclaw/commands/` — handlers for `/provider_model`, `/model`, `/provider_search`, `/copy`
- `iclaw/config.py` — `CONFIG_PATH`, `TOKEN_REFRESH_INTERVAL`, `load_github_token()`

**API endpoints:**
- `https://api.github.com/copilot_internal/v2/token` — Copilot token exchange
- `https://api.githubcopilot.com/chat/completions` — Chat completions
- `https://api.githubcopilot.com/models` — Available model list
