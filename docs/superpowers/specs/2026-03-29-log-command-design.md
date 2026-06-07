# /log Command Design

## Overview

Add a `/log` command to iclaw that controls output verbosity during REPL sessions. Two levels: `verbose` (show everything) and `info` (minimal output).

## Log Module (`iclaw/log.py`)

New module providing centralized log output control.

- **Levels**: `INFO = 0`, `VERBOSE = 1`
- **Default**: `VERBOSE` (preserves current behavior)
- **State**: Module-level `_level` variable
- **API**:
  - `set_level(level)` / `get_level()` — control current level
  - `log_info(message)` — always prints (errors, replies, command feedback)
  - `log_verbose(message)` — prints only in verbose mode (tool status, debug info)

## `/log` Command (`iclaw/commands/log.py`)

- `/log` — prints current level (e.g. "Log level: verbose")
- `/log verbose` — sets level to VERBOSE
- `/log info` — sets level to INFO
- `/log <invalid>` — prints "Unknown log level: <invalid>. Use 'verbose' or 'info'."
- Persisted to `config.yaml` as `log_level: verbose` or `log_level: info`
- Added to `COMMANDS` list in `completer.py` and `COMMANDS_HELP` in `main.py`

## Call Site Changes

### `web_search.py`
- `[web search] Searching (provider): query` — `log_verbose()`
- `[web search] Fetched: url` — `log_verbose()`
- All `[web search] Error ...` prints across provider functions (`search_ddg`, `search_startpage`, `search_bing`, `search_tavily`, `extract_text_from_url`) — `log_info()` (errors always shown)

### `exec_tool.py`
- `[exec] Running command: {command}` — `log_verbose()`

### `main.py` (tool call loop)
- **New** generic logging before each tool call: `log_verbose(f"[tool] Calling {function_name} with {function_args}")` — shows raw tool inputs (covers all tools including edit which currently has no print)
- **New** generic logging after each tool call: `log_verbose(f"[tool] Result: {result_content}")` — shows raw tool outputs
- Final assistant replies — `log_info()` (always shown)
- `/search` command direct output (when no copilot_token) — `log_info()`
- Errors — `log_info()` (always shown)
- Startup messages — `log_info()` (always shown)

### `commands/*.py`
- Command confirmations (e.g. "Model set to...") — `log_info()` (direct user feedback, always shown)

### `config.py`
- Add `log_level` parameter to `save_session_settings()` signature
- Update all existing call sites of `save_session_settings()` in `main.py` to pass through `log_level`
- Load `log_level` from config on startup, call `log.set_level()` to initialize

### `/status` command in `main.py`
- Add log level to the `/status` output alongside model, provider, etc.

## Message Classification Summary

| Level | What's shown |
|-------|-------------|
| `info` | Final replies, errors, command confirmations, startup messages |
| `verbose` | Everything above + `[web search]` status, `[exec]` status, raw tool call inputs/outputs |

## Files to Create
- `iclaw/log.py`
- `iclaw/commands/log.py`

## Files to Modify
- `iclaw/main.py` — dispatch `/log` command, add tool call logging in agentic loop, add to COMMANDS_HELP, add to /status output
- `iclaw/web_search.py` — replace `print()` with `log_verbose()`/`log_info()`
- `iclaw/exec_tool.py` — replace `print()` with `log_verbose()`
- `iclaw/config.py` — load/save `log_level` setting, update `save_session_settings()` signature
- `iclaw/completer.py` — add `/log` to `COMMANDS`
