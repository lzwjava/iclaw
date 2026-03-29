# Proxy & CA Bundle Support for iclaw

## Problem

iclaw currently has hardcoded proxy settings in `web_search.py` (`127.0.0.1:7890`) and no proxy support at all for GitHub/Copilot API calls in `github_api.py`. There is no way to configure a custom CA bundle for HTTPS certificate verification. Users behind corporate proxies or using self-signed certificates cannot use iclaw.

## Solution

Add `/proxy` and `/ca_bundle` REPL commands that persist settings to config and apply them to all outgoing HTTP requests via a centralized `requests.Session`.

## Design

### Configuration (`config.py`)

Two new keys in `~/.config/iclaw/config.json`:

- `"proxy"` — string URL (e.g., `"http://127.0.0.1:7890"`) or absent/null when disabled
- `"ca_bundle"` — string file path (e.g., `"/path/to/ca-cert.pem"`) or absent/null for system default

`load_session_settings()` returns dict with two new keys: `"proxy"` (default `None`) and `"ca_bundle"` (default `None`).

`save_session_settings()` signature changes to accept keyword arguments for all settings to avoid positional parameter sprawl:

```python
def save_session_settings(*, model_provider, current_model, search_provider, proxy=None, ca_bundle=None):
```

All existing call sites in `main.py` are updated to pass keyword arguments.

### Centralized HTTP Session (`iclaw/http.py`)

New module providing:

- `get_session() -> requests.Session` — returns a module-level session, lazily created on first call. On creation, reads config via `load_session_settings()` and applies proxy/CA bundle settings.
- `reconfigure(proxy=None, ca_bundle=None)` — called when settings change at runtime or at startup; updates `session.proxies` and `session.verify` in-place

Session configuration:

- `session.proxies = {"http": url, "https": url}` when proxy is set; empty dict when not
- `session.verify = ca_bundle_path` when CA bundle is set; `True` (system default) when not
- `session.trust_env = False` — disable `requests`' built-in env var handling so that only explicit `/proxy` configuration is used

Thread safety: `requests.Session` is safe for concurrent reads. The `reconfigure()` call only happens from the main REPL thread. The `ThreadPoolExecutor` in `web_search.py` only issues concurrent `.get()` calls which is safe.

### Call-site changes

**`github_api.py`**: Replace `requests.get()`/`requests.post()` with `http.get_session().get()`/`.post()`. The session carries proxy and verify settings automatically.

**`web_search.py`**: Remove the hardcoded `DEFAULT_PROXY` and `PROXY` dicts. Replace `requests.get(..., proxies=PROXY)` calls with `http.get_session().get(...)` for all search functions:

- `search_ddg()`: Use `http.get_session().get(...)` directly.
- `search_startpage()`: Use `http.get_session().get(...)` directly.
- `search_bing()`: Create a local `requests.Session()` with `s.proxies` and `s.verify` copied from `get_session()`, then set Bing-specific cookies on `s`. This avoids leaking Bing cookies into the shared session.
- `extract_text_from_url()`: Use `http.get_session()` directly (no special cookies needed).
- `search_tavily()`: Uses the `TavilyClient` library which manages its own HTTP calls. Proxy/CA bundle do not apply to Tavily searches. This is acceptable since Tavily is a paid API service typically accessed directly.

### Startup Order (`main.py`)

The startup sequence must ensure proxy/CA bundle are configured before any API calls:

1. `load_session_settings()` — loads proxy, ca_bundle, and other settings
2. `http.reconfigure(proxy=..., ca_bundle=...)` — configures the shared session
3. `get_copilot_token(github_token)` — now uses the configured session

This requires reordering the current `main()` flow so that settings are loaded and `reconfigure()` is called before the initial `get_copilot_token()` call.

### REPL Commands

**`/proxy [url|off]`** in `iclaw/commands/proxy.py`:

- `/proxy` — shows current proxy setting, or "not set" if unset
- `/proxy http://host:port` — sets proxy for both HTTP and HTTPS, persists to config, calls `http.reconfigure()`
- `/proxy off` — clears proxy, persists, calls `http.reconfigure()`
- Validation: check URL starts with `http://` or `https://`. Reject other schemes (e.g., `socks5://`) with a message that SOCKS is not supported.

**`/ca_bundle [path|off]`** in `iclaw/commands/proxy.py` (same module):

- `/ca_bundle` — shows current CA bundle path, or "system default" if unset
- `/ca_bundle /path/to/cert.pem` — validates file exists (prints error if not), resolves to absolute path, persists, calls `http.reconfigure()`. Paths with spaces are supported since `split(maxsplit=1)` preserves the full path.
- `/ca_bundle off` — clears CA bundle (reverts to system default), persists, calls `http.reconfigure()`

Both command handlers follow the pattern of existing commands: they receive current state, return updated state, and the caller (`main.py`) handles persistence via `save_session_settings()`. They do NOT call `save_session_settings` or `http.reconfigure()` internally — `main.py` does that after the handler returns, consistent with how `/model` and `/search_provider` work.

### REPL Integration (`main.py`)

Command dispatch: Since `/proxy` and `/ca_bundle` take inline arguments, match with `user_input == "/proxy" or user_input.startswith("/proxy ")` (note the trailing space to avoid matching `/proxy_other`). Parse with `split(maxsplit=1)`.

```python
if user_input == "/proxy" or user_input.startswith("/proxy "):
    parts = user_input.split(maxsplit=1)
    arg = parts[1] if len(parts) > 1 else None
    proxy = handle_proxy_command(proxy, arg)
    http.reconfigure(proxy=proxy, ca_bundle=ca_bundle)
    save_session_settings(model_provider=model_provider, current_model=current_model,
                          search_provider=search_provider, proxy=proxy, ca_bundle=ca_bundle)
    continue
```

`proxy` and `ca_bundle` are tracked as local variables in `main()`, alongside `model_provider`, `current_model`, and `search_provider`.

`/status` output shows:
- `proxy: http://host:port` or `proxy: (not set)`
- `ca_bundle: /path/to/cert.pem` or `ca_bundle: (system default)`

`COMMANDS_HELP` updated to include entries for `/proxy` and `/ca_bundle`.

Error handling for unreachable proxies: No connectivity test at set time. If the proxy is unreachable, the next API call will raise a `ConnectionError` which is caught by the existing `except Exception` handler in the REPL loop and printed to stderr.

### Completer (`completer.py`)

Add `/proxy` and `/ca_bundle` to the `COMMANDS` list.

### Testing

- Unit tests for `config.py`: load/save proxy and ca_bundle settings round-trip, defaults when absent
- Unit tests for `/proxy` and `/ca_bundle` command handlers: set, show, clear, invalid input behaviors
- Unit tests for `iclaw/http.py`: lazy creation, `reconfigure()` updates session proxies and verify attributes, `trust_env` is False
- Update existing `github_api.py` tests to mock `http.get_session()` instead of `requests` directly

### Out of Scope

- SOCKS proxy support (rejected with message if attempted)
- Per-request proxy overrides
- Proxy authentication (user:pass in URL is supported by `requests` natively)
- Environment variable fallback — the explicit `os.environ.get()` code in `web_search.py` is removed, and `session.trust_env = False` prevents `requests` from reading env vars. Users should use `/proxy` instead.
- Proxy for Tavily API (uses its own HTTP client)
- Certificate format validation (delegated to `requests`/`urllib3` at request time)
- Proxy connectivity test at set time
