import os
import sys


def _is_binary(data):
    return b"\x00" in data


def _highlighted_lines(text, path):
    try:
        from pygments import highlight
        from pygments.formatters import Terminal256Formatter
        from pygments.lexers import TextLexer, get_lexer_for_filename
        from pygments.util import ClassNotFound
    except ImportError:
        return text.splitlines()
    try:
        lexer = get_lexer_for_filename(path, stripnl=False)
    except ClassNotFound:
        lexer = TextLexer(stripnl=False)
    formatter = Terminal256Formatter(style="monokai")
    highlighted = highlight(text, lexer, formatter)
    return highlighted.splitlines()


def handle_read_command(arg):
    if not arg:
        print("Usage: /read <path>", file=sys.stderr)
        return

    path = arg.strip()
    if path.startswith("@"):
        path = path[1:]

    if not os.path.exists(path):
        print(f"No such file: {path}", file=sys.stderr)
        return
    if os.path.isdir(path):
        print(f"Is a directory: {path}", file=sys.stderr)
        return

    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        return

    if _is_binary(raw):
        print(f"Binary file: {path} ({len(raw)} bytes)", file=sys.stderr)
        return

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")

    plain_lines = text.splitlines()
    highlighted_lines = _highlighted_lines(text, path)
    line_count = len(plain_lines)
    print(f"\n{path} — {line_count} lines")
    width = len(str(line_count)) if line_count else 1
    for i, line in enumerate(highlighted_lines, 1):
        print(f"\033[2m{i:>{width}}\033[0m  {line}")
    print()
