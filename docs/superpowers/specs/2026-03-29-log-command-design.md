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
  - `log(message, level=VERBOSE)` — prints if `_level >= level`
  - `log_info(message)` — always prints (errors, replies, command feedback)
  - `log_verbose(message)` — prints only in verbose mode (tool status, debug info)

## `/log` Command (`iclaw/commands/log.py`)

- `/log` — prints current level (e.g. "Log level: verbose")
- `/log verbose` — sets level to VERBOSE
- `/log info` — sets level to INFO
- Persisted to `config.json` as `"log_level": "verbose"` or `"log_level": "info"`
- Added to `COMMANDS` list in `completer.py`

## Call Site Changes

### `web_search.py`
- `[web search] Searching (provider): query` — `log_verbose()`
- `[web search] Fetched: url` — `log_verbose()`
- `[web search] Error ...` — `log_info()` (errors always shown)

### `exec_tool.py`
- `[exec] Running command: {command}` — `log_verbose()`

### `main.py` (tool call loop)
- Before each tool call: `log_verbose(f"[tool] Calling {function_name} with {function_args}")` — shows raw tool inputs
- After each tool call: `log_verbose(f"[tool] Result: {result_content}")` — shows raw tool outputs
- Final assistant replies — `log_info()` (always shown)
- Errors — `log_info()` (always shown)
- Startup messages — `log_info()` (always shown)

### `commands/*.py`
- Command confirmations (e.g. "Model set to...") — `log_info()` (direct user feedback, always shown)

### `config.py`
- Load `log_level` from config on startup, call `log.set_level()` to initialize
- Save `log_level` when changed via `/log` command

## Message Classification Summary

| Level | What's shown |
|-------|-------------|
| `info` | Final replies, errors, command confirmations, startup messages |
| `verbose` | Everything above + `[web search]` status, `[exec]` status, raw tool call inputs/outputs |

## Files to Create
- `iclaw/log.py`
- `iclaw/commands/log.py`

## Files to Modify
- `iclaw/main.py` — dispatch `/log` command, add tool call logging in agentic loop
- `iclaw/web_search.py` — replace `print()` with `log_verbose()`/`log_info()`
- `iclaw/exec_tool.py` — replace `print()` with `log_verbose()`
- `iclaw/config.py` — load/save `log_level` setting
- `iclaw/completer.py` — add `/log` to `COMMANDS`
