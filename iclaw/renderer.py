"""Markdown rendering for terminal output using rich."""

from rich.console import Console
from rich.markdown import Markdown


def print_markdown(text: str) -> None:
    """Render markdown text to the terminal with formatting.

    Uses rich to render headings, code blocks, lists, bold/italic,
    links, tables, etc. Falls back to plain print if rendering fails.
    """
    if not text or not text.strip():
        print(text or "")
        return

    try:
        console = Console(soft_wrap=True)
        console.print(Markdown(text))
    except Exception:
        # Fallback to plain text if rich rendering fails
        print(text)
