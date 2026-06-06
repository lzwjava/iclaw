"""
Browser automation tool for iclaw using Playwright.

Provides persistent browser sessions with accessibility-tree snapshots,
element interaction via ref IDs, screenshots, and console monitoring.
"""

import base64
import os
import tempfile
from typing import Optional

from iclaw.log import log_verbose

# Lazy imports - playwright may not be installed
_playwright = None
_browser = None
_context = None
_page = None
_console_logs = []
_element_map = {}  # ref_id -> element


def _ensure_playwright():
    """Lazy import and install check."""
    global _playwright
    if _playwright is None:
        try:
            from playwright.sync_api import sync_playwright

            _playwright = sync_playwright()
        except ImportError:
            raise RuntimeError(
                "playwright is not installed. Run: pip install playwright && playwright install chromium"
            )


def _get_browser():
    """Get or create a persistent browser instance."""
    global _browser, _context, _page, _console_logs
    _ensure_playwright()

    if _browser is None:
        pw = _playwright.start()
        headless = os.environ.get("ICLAW_BROWSER_HEADLESS", "1") == "1"
        _browser = pw.chromium.launch(headless=headless)
        _context = _browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        _page = _context.new_page()
        _console_logs = []

        # Capture console messages
        _page.on(
            "console",
            lambda msg: _console_logs.append(
                {
                    "type": msg.type,
                    "text": msg.text,
                }
            ),
        )
        _page.on(
            "pageerror",
            lambda err: _console_logs.append(
                {
                    "type": "error",
                    "text": str(err),
                }
            ),
        )

    return _page


def _build_element_map(page):
    """Build a map of ref_id -> interactive elements on the page."""
    global _element_map
    _element_map = {}

    # Get all interactive elements
    elements = page.query_selector_all(
        "a, button, input, textarea, select, [role='button'], [role='link'], "
        "[role='tab'], [role='menuitem'], [onclick], [tabindex]"
    )

    for i, el in enumerate(elements, 1):
        ref_id = f"@e{i}"
        _element_map[ref_id] = el

    return _element_map


def _get_element_snapshot(page) -> str:
    """Build a text snapshot of the page with ref IDs for interactive elements."""
    _build_element_map(page)

    # Get page title and URL
    title = page.title()
    url = page.url

    # Get accessibility tree
    snapshot_lines = [f"Page: {title}", f"URL: {url}", ""]

    # Get all visible text elements with their ref IDs
    result = page.evaluate("""() => {
        const items = [];
        let refCounter = 0;

        function isVisible(el) {
            const style = window.getComputedStyle(el);
            return style.display !== 'none' && style.visibility !== 'hidden' && el.offsetHeight > 0;
        }

        function getRefId(el) {
            const tag = el.tagName.toLowerCase();
            const isInteractive = ['a', 'button', 'input', 'textarea', 'select'].includes(tag) ||
                el.getAttribute('role') === 'button' ||
                el.getAttribute('role') === 'link' ||
                el.hasAttribute('onclick') ||
                el.hasAttribute('tabindex');
            if (isInteractive) {
                refCounter++;
                return '@e' + refCounter;
            }
            return null;
        }

        function walk(node) {
            if (node.nodeType === Node.TEXT_NODE) {
                const text = node.textContent.trim();
                if (text && isVisible(node.parentElement)) {
                    const refId = getRefId(node.parentElement);
                    items.push({type: 'text', text: text, ref: refId, tag: node.parentElement.tagName.toLowerCase()});
                }
                return;
            }

            if (node.nodeType !== Node.ELEMENT_NODE) return;
            if (!isVisible(node)) return;

            const tag = node.tagName.toLowerCase();
            const refId = getRefId(node);

            if (tag === 'input') {
                const inputType = node.type || 'text';
                const value = node.value || '';
                const placeholder = node.placeholder || '';
                items.push({type: 'input', inputType, value, placeholder, ref: refId});
            } else if (tag === 'textarea') {
                items.push({type: 'textarea', value: node.value || '', ref: refId});
            } else if (tag === 'button') {
                items.push({type: 'button', text: node.textContent.trim(), ref: refId});
            } else if (tag === 'a') {
                items.push({type: 'link', text: node.textContent.trim(), href: node.href || '', ref: refId});
            } else if (tag === 'select') {
                const options = Array.from(node.options).map(o => o.textContent.trim());
                items.push({type: 'select', options, ref: refId});
            }

            for (const child of node.childNodes) {
                walk(child);
            }
        }

        walk(document.body);
        return items;
    }""")

    for item in result:
        ref = item.get("ref", "")
        ref_str = f" [{ref}]" if ref else ""

        if item["type"] == "text":
            snapshot_lines.append(f"{item['text']}{ref_str}")
        elif item["type"] == "input":
            val = f" (value: {item['value']})" if item.get("value") else ""
            ph = (
                f" (placeholder: {item['placeholder']})"
                if item.get("placeholder")
                else ""
            )
            snapshot_lines.append(
                f"[input:{item.get('inputType', 'text')}] {val}{ph}{ref_str}"
            )
        elif item["type"] == "textarea":
            val = f" (value: {item['value'][:100]})" if item.get("value") else ""
            snapshot_lines.append(f"[textarea]{val}{ref_str}")
        elif item["type"] == "button":
            snapshot_lines.append(f"[button] {item['text']}{ref_str}")
        elif item["type"] == "link":
            href = f" -> {item['href']}" if item.get("href") else ""
            snapshot_lines.append(f"[link] {item['text']}{href}{ref_str}")
        elif item["type"] == "select":
            opts = ", ".join(item.get("options", [])[:5])
            snapshot_lines.append(f"[select] options: {opts}{ref_str}")

    return "\n".join(snapshot_lines)


# --- Public API functions (called by tool dispatch) ---


def browser_navigate(url: str) -> str:
    """Navigate to a URL and return a snapshot."""
    log_verbose(f"[browser] Navigating to {url}")
    page = _get_browser()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        # networkidle may timeout on heavy pages, that's ok
        pass

    snapshot = _get_element_snapshot(page)
    return f"Navigated to {url}\n\n{snapshot}"


def browser_snapshot(full: bool = False) -> str:
    """Get current page snapshot with element refs."""
    page = _get_browser()
    snapshot = _get_element_snapshot(page)

    if full:
        # Also get full page text
        full_text = page.evaluate("() => document.body.innerText")
        # Truncate to reasonable size
        if len(full_text) > 8000:
            full_text = full_text[:8000] + "\n... (truncated)"
        return f"{snapshot}\n\n--- Full Page Text ---\n{full_text}"

    return snapshot


def browser_click(ref: str) -> str:
    """Click an element by its ref ID."""
    log_verbose(f"[browser] Clicking {ref}")
    page = _get_browser()

    if ref not in _element_map:
        # Try rebuilding the map
        _build_element_map(page)
        if ref not in _element_map:
            return f"Error: Element {ref} not found. Take a new snapshot first."

    try:
        el = _element_map[ref]
        el.scroll_into_view_if_needed()
        el.click(timeout=5000)
        page.wait_for_load_state("domcontentloaded", timeout=5000)
    except Exception:
        pass

    snapshot = _get_element_snapshot(page)
    return f"Clicked {ref}\n\n{snapshot}"


def browser_type(ref: str, text: str, submit: bool = False) -> str:
    """Type text into an element. If submit=True, press Enter after."""
    log_verbose(f"[browser] Typing into {ref}: {text[:50]}...")
    page = _get_browser()

    if ref not in _element_map:
        _build_element_map(page)
        if ref not in _element_map:
            return f"Error: Element {ref} not found. Take a new snapshot first."

    try:
        el = _element_map[ref]
        el.scroll_into_view_if_needed()
        el.click()
        el.fill(text)
        if submit:
            el.press("Enter")
            page.wait_for_load_state("domcontentloaded", timeout=5000)
    except Exception as e:
        return f"Error typing into {ref}: {e}"

    snapshot = _get_element_snapshot(page)
    return f"Typed into {ref}\n\n{snapshot}"


def browser_press(key: str) -> str:
    """Press a keyboard key (Enter, Tab, Escape, ArrowDown, etc.)."""
    log_verbose(f"[browser] Pressing {key}")
    page = _get_browser()

    try:
        page.keyboard.press(key)
        page.wait_for_load_state("domcontentloaded", timeout=3000)
    except Exception:
        pass

    snapshot = _get_element_snapshot(page)
    return f"Pressed {key}\n\n{snapshot}"


def browser_scroll(direction: str = "down") -> str:
    """Scroll the page up or down."""
    page = _get_browser()
    delta = 500 if direction == "down" else -500
    page.evaluate(f"window.scrollBy(0, {delta})")

    snapshot = _get_element_snapshot(page)
    return f"Scrolled {direction}\n\n{snapshot}"


def browser_screenshot(save_path: Optional[str] = None) -> str:
    """Take a screenshot. Returns path to the saved image."""
    page = _get_browser()

    if save_path is None:
        fd, save_path = tempfile.mkstemp(suffix=".png", prefix="iclaw_browser_")
        os.close(fd)

    page.screenshot(path=save_path, full_page=False)

    # Also return a base64 thumbnail for vision models
    with open(save_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    return f"Screenshot saved to {save_path}\nBase64 ({len(b64)} chars): data:image/png;base64,{b64[:200]}..."


def browser_console(clear: bool = False) -> str:
    """Get browser console output."""
    global _console_logs

    if not _console_logs:
        return "Console is empty."

    output = []
    for msg in _console_logs[-50:]:  # Last 50 messages
        prefix = f"[{msg['type']}]"
        output.append(f"{prefix} {msg['text']}")

    if clear:
        _console_logs.clear()

    return "\n".join(output)


def browser_back() -> str:
    """Navigate back in browser history."""
    page = _get_browser()
    page.go_back(wait_until="domcontentloaded", timeout=10000)
    snapshot = _get_element_snapshot(page)
    return f"Navigated back\n\n{snapshot}"


def browser_close() -> str:
    """Close the browser and clean up."""
    global _browser, _context, _page, _console_logs, _element_map

    if _page:
        _page.close()
        _page = None
    if _context:
        _context.close()
        _context = None
    if _browser:
        _browser.close()
        _browser = None
    _console_logs.clear()
    _element_map.clear()

    return "Browser closed."


def dispatch_browser_call(function_name: str, args: dict) -> str:
    """Dispatch a browser tool call to the appropriate function."""
    dispatch = {
        "browser_navigate": lambda a: browser_navigate(a["url"]),
        "browser_snapshot": lambda a: browser_snapshot(a.get("full", False)),
        "browser_click": lambda a: browser_click(a["ref"]),
        "browser_type": lambda a: browser_type(
            a["ref"], a["text"], a.get("submit", False)
        ),
        "browser_press": lambda a: browser_press(a["key"]),
        "browser_scroll": lambda a: browser_scroll(a.get("direction", "down")),
        "browser_screenshot": lambda a: browser_screenshot(),
        "browser_console": lambda a: browser_console(a.get("clear", False)),
        "browser_back": lambda a: browser_back(),
        "browser_close": lambda a: browser_close(),
    }

    handler = dispatch.get(function_name)
    if not handler:
        return f"Unknown browser function: {function_name}"

    try:
        return handler(args)
    except Exception as e:
        return f"Browser error: {e}"
