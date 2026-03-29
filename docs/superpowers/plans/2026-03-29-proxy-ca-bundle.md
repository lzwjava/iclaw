# Proxy & CA Bundle Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `/proxy` and `/ca_bundle` REPL commands that persist to config and route all HTTP requests through a centralized `requests.Session`.

**Architecture:** A new `iclaw/http.py` module owns a lazily-created `requests.Session` whose proxy and verify settings are updated via `reconfigure()`. All call sites (`github_api.py`, `web_search.py`) switch from bare `requests` calls to using this shared session. New REPL commands let users set/clear proxy and CA bundle at runtime.

**Tech Stack:** Python 3, `requests`, `unittest`

**Spec:** `docs/superpowers/specs/2026-03-29-proxy-ca-bundle-design.md`

---

### Task 1: Extend `config.py` with proxy/ca_bundle support

**Files:**
- Modify: `iclaw/config.py`
- Test: `tests/test_config.py` (new file)

- [ ] **Step 1: Write tests for config changes**

Create `tests/test_config.py`:

```python
import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from iclaw.config import load_session_settings, save_session_settings


class TestConfigProxySettings(unittest.TestCase):
    def test_load_defaults_when_no_proxy_or_ca_bundle(self):
        with patch("iclaw.config.CONFIG_PATH") as mp:
            mp.exists.return_value = True
            mp.read_text.return_value = json.dumps({"model_provider": "copilot"})
            settings = load_session_settings()
        self.assertIsNone(settings["proxy"])
        self.assertIsNone(settings["ca_bundle"])

    def test_load_proxy_and_ca_bundle_when_set(self):
        with patch("iclaw.config.CONFIG_PATH") as mp:
            mp.exists.return_value = True
            mp.read_text.return_value = json.dumps({
                "proxy": "http://127.0.0.1:8080",
                "ca_bundle": "/path/to/cert.pem",
            })
            settings = load_session_settings()
        self.assertEqual(settings["proxy"], "http://127.0.0.1:8080")
        self.assertEqual(settings["ca_bundle"], "/path/to/cert.pem")

    def test_save_session_settings_with_proxy_and_ca_bundle(self):
        with patch("iclaw.config.CONFIG_PATH") as mp:
            mp.exists.return_value = True
            mp.read_text.return_value = json.dumps({"github_token": "gt"})
            mp.parent = MagicMock()
            save_session_settings(
                model_provider="copilot",
                current_model="gpt-4o",
                search_provider="duckduckgo",
                proxy="http://proxy:8080",
                ca_bundle="/path/cert.pem",
            )
            written = json.loads(mp.write_text.call_args[0][0])
        self.assertEqual(written["proxy"], "http://proxy:8080")
        self.assertEqual(written["ca_bundle"], "/path/cert.pem")
        self.assertEqual(written["github_token"], "gt")

    def test_save_session_settings_clears_null_proxy(self):
        with patch("iclaw.config.CONFIG_PATH") as mp:
            mp.exists.return_value = True
            mp.read_text.return_value = json.dumps({"proxy": "http://old:1234"})
            mp.parent = MagicMock()
            save_session_settings(
                model_provider="copilot",
                current_model="gpt-4o",
                search_provider="duckduckgo",
                proxy=None,
                ca_bundle=None,
            )
            written = json.loads(mp.write_text.call_args[0][0])
        self.assertIsNone(written["proxy"])
        self.assertIsNone(written["ca_bundle"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests/test_config.py -v`
Expected: FAIL — `save_session_settings` takes positional args, missing proxy/ca_bundle keys.

- [ ] **Step 3: Update `config.py`**

Modify `load_session_settings()` to add proxy and ca_bundle keys:

```python
def load_session_settings() -> dict:
    config = _load_config()
    return {
        "model_provider": config.get("model_provider", "copilot"),
        "current_model": config.get("current_model", "gpt-5.2"),
        "search_provider": config.get("search_provider", "duckduckgo"),
        "proxy": config.get("proxy"),
        "ca_bundle": config.get("ca_bundle"),
    }
```

Change `save_session_settings()` to accept both positional (backward-compat) and keyword arguments. The `*` keyword-only conversion happens in Task 6 when all call sites are updated simultaneously.

```python
def save_session_settings(
    model_provider, current_model, search_provider, proxy=None, ca_bundle=None
) -> None:
    config = _load_config()
    config["model_provider"] = model_provider
    config["current_model"] = current_model
    config["search_provider"] = search_provider
    config["proxy"] = proxy
    config["ca_bundle"] = ca_bundle
    _save_config(config)
```

- [ ] **Step 4: Run ALL tests to verify nothing is broken**

Run: `python3 -m unittest discover tests -v`
Expected: All tests PASS — existing `main.py` positional calls still work because we kept positional parameters.

- [ ] **Step 5: Commit**

```bash
git add iclaw/config.py tests/test_config.py
git commit -m "feat(config): add proxy and ca_bundle settings"
```

---

### Task 2: Create centralized HTTP session module (`iclaw/http.py`)

**Files:**
- Create: `iclaw/http.py`
- Test: `tests/test_http.py` (new file)

- [ ] **Step 1: Write tests for http module**

Create `tests/test_http.py`:

```python
import unittest
from unittest.mock import patch

from iclaw import http


class TestHttpSession(unittest.TestCase):
    def setUp(self):
        http._session = None

    def test_get_session_returns_session(self):
        with patch("iclaw.http.load_session_settings", return_value={
            "proxy": None, "ca_bundle": None,
            "model_provider": "copilot", "current_model": "gpt-4o",
            "search_provider": "duckduckgo",
        }):
            s = http.get_session()
        self.assertFalse(s.trust_env)
        self.assertEqual(s.proxies, {})
        self.assertTrue(s.verify)

    def test_get_session_with_proxy(self):
        with patch("iclaw.http.load_session_settings", return_value={
            "proxy": "http://proxy:8080", "ca_bundle": None,
            "model_provider": "copilot", "current_model": "gpt-4o",
            "search_provider": "duckduckgo",
        }):
            s = http.get_session()
        self.assertEqual(s.proxies, {"http": "http://proxy:8080", "https": "http://proxy:8080"})

    def test_get_session_with_ca_bundle(self):
        with patch("iclaw.http.load_session_settings", return_value={
            "proxy": None, "ca_bundle": "/path/cert.pem",
            "model_provider": "copilot", "current_model": "gpt-4o",
            "search_provider": "duckduckgo",
        }):
            s = http.get_session()
        self.assertEqual(s.verify, "/path/cert.pem")

    def test_reconfigure_updates_session(self):
        with patch("iclaw.http.load_session_settings", return_value={
            "proxy": None, "ca_bundle": None,
            "model_provider": "copilot", "current_model": "gpt-4o",
            "search_provider": "duckduckgo",
        }):
            s = http.get_session()
        self.assertEqual(s.proxies, {})
        http.reconfigure(proxy="http://new:1234", ca_bundle="/new/cert.pem")
        self.assertEqual(s.proxies, {"http": "http://new:1234", "https": "http://new:1234"})
        self.assertEqual(s.verify, "/new/cert.pem")

    def test_reconfigure_clears_settings(self):
        with patch("iclaw.http.load_session_settings", return_value={
            "proxy": "http://proxy:8080", "ca_bundle": "/cert.pem",
            "model_provider": "copilot", "current_model": "gpt-4o",
            "search_provider": "duckduckgo",
        }):
            s = http.get_session()
        http.reconfigure(proxy=None, ca_bundle=None)
        self.assertEqual(s.proxies, {})
        self.assertTrue(s.verify)

    def test_get_session_is_lazy_singleton(self):
        with patch("iclaw.http.load_session_settings", return_value={
            "proxy": None, "ca_bundle": None,
            "model_provider": "copilot", "current_model": "gpt-4o",
            "search_provider": "duckduckgo",
        }):
            s1 = http.get_session()
            s2 = http.get_session()
        self.assertIs(s1, s2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests/test_http.py -v`
Expected: FAIL — `iclaw.http` module does not exist.

- [ ] **Step 3: Create `iclaw/http.py`**

```python
import requests

from iclaw.config import load_session_settings

_session = None


def get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        _session.trust_env = False
        settings = load_session_settings()
        reconfigure(proxy=settings.get("proxy"), ca_bundle=settings.get("ca_bundle"))
    return _session


def reconfigure(proxy=None, ca_bundle=None):
    s = get_session()
    if proxy:
        s.proxies = {"http": proxy, "https": proxy}
    else:
        s.proxies = {}
    if ca_bundle:
        s.verify = ca_bundle
    else:
        s.verify = True
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests/test_http.py -v`
Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add iclaw/http.py tests/test_http.py
git commit -m "feat(http): add centralized HTTP session with proxy/CA bundle support"
```

---

### Task 3: Migrate `github_api.py` to use shared session

**Files:**
- Modify: `iclaw/github_api.py`
- Modify: `tests/test_github_api.py`

- [ ] **Step 1: Update tests to mock `http.get_session()`**

In `tests/test_github_api.py`, change all `@patch("iclaw.github_api.requests.get")` and `@patch("iclaw.github_api.requests.post")` to mock the session object returned by `get_session()`.

Replace the entire file with:

```python
import unittest
from unittest.mock import MagicMock, patch

from iclaw import github_api


def _mock_session(mock_response):
    session = MagicMock()
    session.get.return_value = mock_response
    session.post.return_value = mock_response
    return session


class TestGithubApi(unittest.TestCase):
    @patch("iclaw.github_api.http.get_session")
    def test_get_copilot_token_success(self, mock_gs):
        mock_gs.return_value = _mock_session(
            MagicMock(ok=True, json=lambda: {"token": "t"})
        )
        self.assertEqual(github_api.get_copilot_token("gt"), "t")

    @patch("iclaw.github_api.http.get_session")
    def test_get_copilot_token_failure(self, mock_gs):
        mock_gs.return_value = _mock_session(
            MagicMock(ok=False, status_code=401, reason="Unauthorized")
        )
        with self.assertRaises(RuntimeError):
            github_api.get_copilot_token("it")

    @patch("iclaw.github_api.http.get_session")
    def test_get_models(self, mock_gs):
        mock_gs.return_value = _mock_session(
            MagicMock(ok=True, json=lambda: {"data": [{"id": "m"}]})
        )
        self.assertEqual(github_api.get_models("t")[0]["id"], "m")

    @patch("iclaw.github_api.http.get_session")
    def test_get_models_failure(self, mock_gs):
        mock_gs.return_value = _mock_session(
            MagicMock(ok=False, status_code=403, reason="Forbidden")
        )
        with self.assertRaises(RuntimeError):
            github_api.get_models("t")

    @patch("iclaw.github_api.http.get_session")
    def test_chat(self, mock_gs):
        mock_gs.return_value = _mock_session(
            MagicMock(ok=True, json=lambda: {"choices": [{"message": {"content": "h"}}]})
        )
        self.assertEqual(github_api.chat([], "t")["content"], "h")

    @patch("iclaw.github_api.http.get_session")
    def test_chat_with_tools(self, mock_gs):
        mock_gs.return_value = _mock_session(
            MagicMock(ok=True, json=lambda: {"choices": [{"message": {"content": "h"}}]})
        )
        result = github_api.chat([], "t", tools=[{"type": "function"}])
        self.assertEqual(result["content"], "h")

    @patch("iclaw.github_api.http.get_session")
    def test_chat_failure(self, mock_gs):
        mock_gs.return_value = _mock_session(
            MagicMock(ok=False, status_code=500, reason="Server Error", text="err")
        )
        with self.assertRaises(RuntimeError):
            github_api.chat([], "t")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests/test_github_api.py -v`
Expected: FAIL — `github_api` still imports `requests` directly.

- [ ] **Step 3: Update `github_api.py` to use shared session**

Replace `import requests` with `from iclaw import http` and update all three functions:

```python
import os

from iclaw import http

GITHUB_API_BASE = os.environ.get("ICLAW_GITHUB_API_BASE", "https://api.github.com")
COPILOT_API_BASE = os.environ.get(
    "ICLAW_COPILOT_API_BASE", "https://api.githubcopilot.com"
)

COPILOT_HEADERS = {
    "Content-Type": "application/json",
    "Editor-Version": "vscode/1.85.0",
    "Editor-Plugin-Version": "copilot/1.155.0",
    "User-Agent": "GithubCopilot/1.155.0",
    "Copilot-Integration-Id": "vscode-chat",
}


def get_copilot_token(github_token):
    resp = http.get_session().get(
        f"{GITHUB_API_BASE}/copilot_internal/v2/token",
        headers={
            "Authorization": f"Bearer {github_token}",
            "Editor-Version": "vscode/1.85.0",
            "Editor-Plugin-Version": "copilot/1.155.0",
            "User-Agent": "GithubCopilot/1.155.0",
        },
    )
    if not resp.ok:
        raise RuntimeError(
            f"Failed to get Copilot token: {resp.status_code} {resp.reason}"
        )
    return resp.json()["token"]


def get_models(copilot_token):
    resp = http.get_session().get(
        f"{COPILOT_API_BASE}/models",
        headers={"Authorization": f"Bearer {copilot_token}", **COPILOT_HEADERS},
    )
    if not resp.ok:
        raise RuntimeError(f"Failed to get models: {resp.status_code} {resp.reason}")
    return resp.json().get("data", [])


def chat(messages, copilot_token, model="gpt-4o", tools=None):
    payload = {"model": model, "messages": messages, "stream": False}
    if tools:
        payload["tools"] = tools

    resp = http.get_session().post(
        f"{COPILOT_API_BASE}/chat/completions",
        headers={"Authorization": f"Bearer {copilot_token}", **COPILOT_HEADERS},
        json=payload,
    )
    if not resp.ok:
        raise RuntimeError(
            f"Chat API error: {resp.status_code} {resp.reason}\n{resp.text}"
        )
    return resp.json()["choices"][0]["message"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests/test_github_api.py -v`
Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add iclaw/github_api.py tests/test_github_api.py
git commit -m "refactor(github_api): use centralized HTTP session"
```

---

### Task 4: Migrate `web_search.py` to use shared session

**Files:**
- Modify: `iclaw/web_search.py`

- [ ] **Step 1: Remove hardcoded proxy and update `search_ddg`, `search_startpage`, `extract_text_from_url`**

In `iclaw/web_search.py`:

1. Remove `import requests` (only keep it for the Bing local session)
2. Remove `DEFAULT_PROXY` and `PROXY` dicts (lines 10-14)
3. Add `import requests` back only inside `search_bing` for the local session, and add `from iclaw import http` at the top
4. Update all functions:

At the top of the file, replace:

```python
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from readability import Document

# Configuration
DEFAULT_PROXY = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
PROXY = {
    "http": os.environ.get("HTTP_PROXY", DEFAULT_PROXY["http"]),
    "https": os.environ.get("HTTPS_PROXY", DEFAULT_PROXY["https"]),
}
```

With:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from readability import Document

from iclaw import http
```

In `search_ddg()`, change:
```python
res = requests.get(url, headers=HEADERS, proxies=PROXY, timeout=10)
```
to:
```python
res = http.get_session().get(url, headers=HEADERS, timeout=10)
```

In `search_startpage()`, change:
```python
res = requests.get(
    url, params=params, headers=HEADERS, proxies=PROXY, timeout=10
)
```
to:
```python
res = http.get_session().get(
    url, params=params, headers=HEADERS, timeout=10
)
```

In `extract_text_from_url()`, change:
```python
session = requests.Session()
res = session.get(url, headers=HEADERS, proxies=PROXY, timeout=15)
```
to:
```python
res = http.get_session().get(url, headers=HEADERS, timeout=15)
```

- [ ] **Step 2: Update `search_bing` to use local session with copied proxy/verify settings**

In `search_bing()`, change:
```python
session = requests.Session()
session.cookies.set("SRCHHPGUSR", "SRCHLANG=EN&WLS=2", domain=".bing.com")
session.cookies.set("_EDGE_S", "mkt=en-us", domain=".bing.com")

res = session.get(url, headers=HEADERS, proxies=PROXY, timeout=10)
```
to:
```python
shared = http.get_session()
session = requests.Session()
session.proxies = dict(shared.proxies)
session.verify = shared.verify
session.cookies.set("SRCHHPGUSR", "SRCHLANG=EN&WLS=2", domain=".bing.com")
session.cookies.set("_EDGE_S", "mkt=en-us", domain=".bing.com")

res = session.get(url, headers=HEADERS, timeout=10)
```

- [ ] **Step 3: Update `tests/test_web_search.py` mocks**

The existing tests mock `iclaw.web_search.requests.get` for DDG/Startpage and `iclaw.web_search.requests.Session` for Bing/extract_text. After our changes:
- DDG and Startpage now use `http.get_session().get()` — change mocks to `iclaw.web_search.http.get_session`
- extract_text_from_url now uses `http.get_session().get()` — same change
- Bing still creates a local `requests.Session()` — keep `iclaw.web_search.requests.Session` mock but also mock `http.get_session` since Bing copies from the shared session

In `tests/test_web_search.py`, make these changes:

**DDG tests** — change `@patch("iclaw.web_search.requests.get")` to `@patch("iclaw.web_search.http.get_session")` and update the mock setup:

```python
@patch("iclaw.web_search.http.get_session")
def test_search_ddg(self, mock_gs):
    mock_session = MagicMock()
    mock_gs.return_value = mock_session
    mock_session.get.return_value = MagicMock(
        ok=True,
        text='<html><div class="result__title"><a class="result__a" href="u">T</a></div></html>',
    )
    results = web_search.search_ddg("q", num_results=1)
    self.assertEqual(len(results), 1)
    self.assertEqual(results[0]["url"], "u")
```

Apply the same pattern for `test_search_ddg_with_redirect_url`, `test_search_ddg_double_slash_url`, `test_search_ddg_error`.

**Startpage tests** — same change from `requests.get` to `http.get_session`:

```python
@patch("iclaw.web_search.http.get_session")
def test_search_startpage(self, mock_gs):
    mock_session = MagicMock()
    mock_gs.return_value = mock_session
    mock_session.get.return_value = MagicMock(
        ok=True,
        text='<html><div class="result"><a class="result-link" href="http://u"><div class="wgl-title">T</div></a></div></html>',
    )
    results = web_search.search_startpage("q", num_results=1)
    self.assertEqual(len(results), 1)
```

Apply same for `test_search_startpage_error`.

**Bing tests** — keep `@patch("iclaw.web_search.requests.Session")` but add `@patch("iclaw.web_search.http.get_session")`:

```python
@patch("iclaw.web_search.http.get_session")
@patch("iclaw.web_search.requests.Session")
def test_search_bing(self, mock_session, mock_gs):
    mock_shared = MagicMock()
    mock_shared.proxies = {}
    mock_shared.verify = True
    mock_gs.return_value = mock_shared
    mock_s = MagicMock()
    mock_session.return_value = mock_s
    mock_s.get.return_value = MagicMock(
        ok=True,
        text='<html><li class="b_algo"><h2><a href="http://u">T</a></h2></li></html>',
    )
    results = web_search.search_bing("q", num_results=1)
    self.assertEqual(len(results), 1)
```

Apply same for `test_search_bing_double_slash`, `test_search_bing_error`.

**extract_text tests** — change `@patch("iclaw.web_search.requests.Session")` to `@patch("iclaw.web_search.http.get_session")` and update mock setup to return a session mock directly:

```python
@patch("iclaw.web_search.http.get_session")
def test_extract_text(self, mock_gs):
    mock_session = MagicMock()
    mock_gs.return_value = mock_session
    mock_session.get.return_value = MagicMock(
        ok=True,
        status_code=200,
        text='<html><div id="firstHeading">T</div></html>',
        apparent_encoding="u8",
    )
    self.assertIn(
        "T", web_search.extract_text_from_url("https://en.wikipedia.org/wiki/T")
    )
```

Apply the same pattern for all other `extract_text_*` tests (`test_extract_text_non_200`, `test_extract_text_exception`, `test_extract_text_zhihu`, `test_extract_text_github`, `test_extract_text_baidu_zhidao`).

For `test_extract_text_generic_readability` and `test_extract_text_generic_fallback` and `test_extract_text_body_fallback`, change `@patch("iclaw.web_search.requests.Session")` to `@patch("iclaw.web_search.http.get_session")` but keep the `@patch("iclaw.web_search.Document")` decorator.

- [ ] **Step 4: Run all tests**

Run: `python3 -m unittest discover tests -v`
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add iclaw/web_search.py tests/test_web_search.py
git commit -m "refactor(web_search): use centralized HTTP session, remove hardcoded proxy"
```

---

### Task 5: Add `/proxy` and `/ca_bundle` command handlers

**Files:**
- Create: `iclaw/commands/proxy.py`
- Test: `tests/test_proxy_commands.py` (new file)

- [ ] **Step 1: Write tests for proxy command handlers**

Create `tests/test_proxy_commands.py`:

```python
import os
import unittest

from iclaw.commands.proxy import handle_proxy_command, handle_ca_bundle_command


class TestHandleProxyCommand(unittest.TestCase):
    def test_show_current_proxy(self):
        result = handle_proxy_command("http://proxy:8080", None)
        self.assertEqual(result, "http://proxy:8080")

    def test_show_no_proxy(self):
        result = handle_proxy_command(None, None)
        self.assertIsNone(result)

    def test_set_proxy(self):
        result = handle_proxy_command(None, "http://new:1234")
        self.assertEqual(result, "http://new:1234")

    def test_set_https_proxy(self):
        result = handle_proxy_command(None, "https://secure:4321")
        self.assertEqual(result, "https://secure:4321")

    def test_clear_proxy(self):
        result = handle_proxy_command("http://old:1234", "off")
        self.assertIsNone(result)

    def test_reject_socks_proxy(self):
        result = handle_proxy_command(None, "socks5://proxy:1080")
        self.assertIsNone(result)

    def test_reject_invalid_scheme(self):
        result = handle_proxy_command(None, "ftp://proxy:21")
        self.assertIsNone(result)


class TestHandleCaBundleCommand(unittest.TestCase):
    def test_show_current_ca_bundle(self):
        result = handle_ca_bundle_command("/path/cert.pem", None)
        self.assertEqual(result, "/path/cert.pem")

    def test_show_no_ca_bundle(self):
        result = handle_ca_bundle_command(None, None)
        self.assertIsNone(result)

    def test_set_ca_bundle(self):
        # Use a file that actually exists
        path = os.path.abspath(__file__)
        result = handle_ca_bundle_command(None, path)
        self.assertEqual(result, path)

    def test_set_ca_bundle_nonexistent_file(self):
        result = handle_ca_bundle_command(None, "/nonexistent/cert.pem")
        self.assertIsNone(result)

    def test_clear_ca_bundle(self):
        result = handle_ca_bundle_command("/path/cert.pem", "off")
        self.assertIsNone(result)

    def test_set_ca_bundle_resolves_relative_path(self):
        # Use current file as a known existing file
        rel_path = os.path.relpath(__file__)
        result = handle_ca_bundle_command(None, rel_path)
        self.assertEqual(result, os.path.abspath(rel_path))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests/test_proxy_commands.py -v`
Expected: FAIL — module `iclaw.commands.proxy` does not exist.

- [ ] **Step 3: Create `iclaw/commands/proxy.py`**

```python
import os


def handle_proxy_command(current_proxy, arg):
    if arg is None:
        if current_proxy:
            print(f"  proxy: {current_proxy}")
        else:
            print("  proxy: (not set)")
        return current_proxy

    if arg == "off":
        print("  Proxy cleared.")
        return None

    if not (arg.startswith("http://") or arg.startswith("https://")):
        print(f"  Invalid proxy URL: {arg}")
        print("  Only http:// and https:// schemes are supported.")
        return current_proxy

    print(f"  Proxy set to {arg}")
    return arg


def handle_ca_bundle_command(current_ca_bundle, arg):
    if arg is None:
        if current_ca_bundle:
            print(f"  ca_bundle: {current_ca_bundle}")
        else:
            print("  ca_bundle: (system default)")
        return current_ca_bundle

    if arg == "off":
        print("  CA bundle cleared. Using system default.")
        return None

    abs_path = os.path.abspath(arg)
    if not os.path.isfile(abs_path):
        print(f"  File not found: {abs_path}")
        return current_ca_bundle

    print(f"  CA bundle set to {abs_path}")
    return abs_path
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests/test_proxy_commands.py -v`
Expected: All 13 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add iclaw/commands/proxy.py tests/test_proxy_commands.py
git commit -m "feat(commands): add /proxy and /ca_bundle command handlers"
```

---

### Task 6: Integrate commands into REPL (`main.py`) and completer

**Files:**
- Modify: `iclaw/main.py`
- Modify: `iclaw/completer.py`

- [ ] **Step 1: Update `main.py` imports and startup order**

Add new imports at the top of `main.py`:

```python
from iclaw import http
from iclaw.commands.proxy import handle_proxy_command, handle_ca_bundle_command
```

- [ ] **Step 2: Update `COMMANDS_HELP` list**

Add two entries before `("/status", ...)`:

```python
("/proxy", "Set HTTP/HTTPS proxy (usage: /proxy [url|off])"),
("/ca_bundle", "Set CA bundle for HTTPS (usage: /ca_bundle [path|off])"),
```

- [ ] **Step 3: Update startup sequence in `main()`**

After `load_session_settings()`, extract proxy and ca_bundle, and call `reconfigure()` before `get_copilot_token()`. Change:

```python
settings = load_session_settings()
model_provider = settings["model_provider"]
current_model = settings["current_model"]
search_provider = settings["search_provider"]

if github_token:
```

To:

```python
settings = load_session_settings()
model_provider = settings["model_provider"]
current_model = settings["current_model"]
search_provider = settings["search_provider"]
proxy = settings["proxy"]
ca_bundle = settings["ca_bundle"]
http.reconfigure(proxy=proxy, ca_bundle=ca_bundle)

if github_token:
```

- [ ] **Step 4: Convert `save_session_settings()` to keyword-only and update all call sites**

Now that we're updating all call sites anyway, convert the function signature to keyword-only in `iclaw/config.py`:

```python
def save_session_settings(
    *, model_provider, current_model, search_provider, proxy=None, ca_bundle=None
) -> None:
```

Then update the 3 existing calls in `main.py` from positional to keyword args:

```python
# Line 94 (in /model_provider handler):
save_session_settings(
    model_provider=model_provider, current_model=current_model,
    search_provider=search_provider, proxy=proxy, ca_bundle=ca_bundle,
)

# Line 98 (in /model handler):
save_session_settings(
    model_provider=model_provider, current_model=current_model,
    search_provider=search_provider, proxy=proxy, ca_bundle=ca_bundle,
)

# Line 102 (in /search_provider handler):
save_session_settings(
    model_provider=model_provider, current_model=current_model,
    search_provider=search_provider, proxy=proxy, ca_bundle=ca_bundle,
)
```

- [ ] **Step 5: Add `/proxy` and `/ca_bundle` command handlers in the REPL loop**

Add these blocks before the `/status` handler:

```python
if user_input == "/proxy" or user_input.startswith("/proxy "):
    parts = user_input.split(maxsplit=1)
    arg = parts[1] if len(parts) > 1 else None
    proxy = handle_proxy_command(proxy, arg)
    http.reconfigure(proxy=proxy, ca_bundle=ca_bundle)
    save_session_settings(
        model_provider=model_provider, current_model=current_model,
        search_provider=search_provider, proxy=proxy, ca_bundle=ca_bundle,
    )
    continue
if user_input == "/ca_bundle" or user_input.startswith("/ca_bundle "):
    parts = user_input.split(maxsplit=1)
    arg = parts[1] if len(parts) > 1 else None
    ca_bundle = handle_ca_bundle_command(ca_bundle, arg)
    http.reconfigure(proxy=proxy, ca_bundle=ca_bundle)
    save_session_settings(
        model_provider=model_provider, current_model=current_model,
        search_provider=search_provider, proxy=proxy, ca_bundle=ca_bundle,
    )
    continue
```

- [ ] **Step 6: Update `/status` output**

Change the `/status` block to add proxy and ca_bundle:

```python
if user_input == "/status":
    print(f"  model_provider:  {model_provider}")
    print(f"  model:           {current_model}")
    print(f"  search_provider: {search_provider}")
    print(f"  proxy:           {proxy or '(not set)'}")
    print(f"  ca_bundle:       {ca_bundle or '(system default)'}")
    print(f"  cwd:             {os.getcwd()}")
    print()
    continue
```

- [ ] **Step 7: Update `completer.py`**

In `iclaw/completer.py`, add `/proxy` and `/ca_bundle` to the `COMMANDS` list:

```python
COMMANDS = [
    "/model_provider",
    "/model",
    "/search_provider",
    "/proxy",
    "/ca_bundle",
    "/copy",
    "/status",
    "/help",
    ".exit",
]
```

- [ ] **Step 8: Run all tests and fix `test_main.py` mock issues**

Run: `python3 -m unittest discover tests -v`

The `test_main.py` tests will likely fail because `main()` now calls `http.reconfigure()` at startup. Add `@patch("iclaw.main.http")` to every test that calls `main.main()`. This mocks the entire `http` module so `reconfigure()` is a no-op.

For example, `test_main_cli` becomes:
```python
@patch("iclaw.main.chat")
@patch("iclaw.main.load_github_token")
@patch("iclaw.main.PromptSession")
@patch("iclaw.main.http")
def test_main_cli(self, mock_http, mock_ps, mock_load, mock_chat):
```

Apply this pattern to all tests in `test_main.py` that invoke `main.main()`.

- [ ] **Step 9: Commit**

```bash
git add iclaw/main.py iclaw/completer.py
git commit -m "feat(main): integrate /proxy and /ca_bundle commands into REPL"
```

---

### Task 7: Final verification and fix any broken tests

**Files:**
- Possibly modify: `tests/test_main.py`, `tests/test_web_search.py`

- [ ] **Step 1: Run entire test suite**

Run: `python3 -m unittest discover tests -v`

- [ ] **Step 2: Fix any failing tests**

Common issues to expect:
- `tests/test_main.py` tests may fail because `main()` now calls `http.reconfigure()` — add `patch("iclaw.main.http")` to test decorators that need it
- `tests/test_web_search.py` tests may fail if they mock `requests.get` directly — update to mock `http.get_session()` instead

- [ ] **Step 3: Run tests again to confirm all pass**

Run: `python3 -m unittest discover tests -v`
Expected: All tests PASS.

- [ ] **Step 4: Run linter and formatter**

```bash
ruff check .
ruff format .
```

- [ ] **Step 5: Commit any fixes**

```bash
git add -u
git commit -m "fix(tests): update test mocks for centralized HTTP session"
```
