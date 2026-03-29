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

`load_session_settings()` and `save_session_settings()` are extended to include `proxy` and `ca_bundle` fields.

### Centralized HTTP Session (`iclaw/http.py`)

New module providing:

- `get_session() -> requests.Session` — returns a module-level session configured with proxy and CA bundle settings from config
- `reconfigure()` — called when settings change at runtime; updates `session.proxies` and `session.verify` in-place

Session configuration:

- `session.proxies = {"http": url, "https": url}` when proxy is set; empty dict when not
- `session.verify = ca_bundle_path` when CA bundle is set; `True` (system default) when not

### Call-site changes

**`github_api.py`**: Replace `requests.get()`/`requests.post()` with `http.get_session().get()`/`.post()`. The session carries proxy and verify settings automatically.

**`web_search.py`**: Remove the hardcoded `DEFAULT_PROXY` and `PROXY` dicts. Replace all `requests.get(..., proxies=PROXY)` and inline `requests.Session()` usage with `http.get_session().get(...)` / `http.get_session().post(...)`.

### REPL Commands

**`/proxy [url|off]`** in `iclaw/commands/proxy.py`:

- `/proxy` — shows current proxy setting
- `/proxy http://host:port` — sets proxy for both HTTP and HTTPS, persists to config, calls `http.reconfigure()`
- `/proxy off` — clears proxy, persists, calls `http.reconfigure()`

**`/ca_bundle [path|off]`** in `iclaw/commands/proxy.py` (same module):

- `/ca_bundle` — shows current CA bundle path
- `/ca_bundle /path/to/cert.pem` — validates file exists, sets CA bundle, persists, calls `http.reconfigure()`
- `/ca_bundle off` — clears CA bundle (reverts to system default), persists, calls `http.reconfigure()`

### REPL Integration (`main.py`)

- Load proxy/ca_bundle from `load_session_settings()` at startup
- Pass them to `http.reconfigure()` during initialization
- Add command handlers for `/proxy` and `/ca_bundle` that parse arguments, delegate to command handlers, and call `save_session_settings()`
- Update `/status` output to display current proxy and ca_bundle values

### Completer (`completer.py`)

Add `/proxy` and `/ca_bundle` to the `COMMANDS` list.

### Testing

- Unit tests for `config.py`: load/save proxy and ca_bundle settings round-trip
- Unit tests for `/proxy` and `/ca_bundle` command handlers: set, show, clear behaviors
- Unit tests for `iclaw/http.py`: `reconfigure()` updates session proxies and verify attributes
- Update existing `github_api.py` tests to mock `http.get_session()` instead of `requests` directly

### Out of Scope

- SOCKS proxy support
- Per-request proxy overrides
- Proxy authentication (user:pass in URL is supported by `requests` natively)
- Environment variable fallback (HTTP_PROXY, HTTPS_PROXY)
