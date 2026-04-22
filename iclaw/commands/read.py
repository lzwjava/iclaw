import os
import sys


def _is_binary(data):
    return b"\x00" in data


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

    lines = text.splitlines()
    print(f"\n{path} — {len(lines)} lines")
    width = len(str(len(lines))) if lines else 1
    for i, line in enumerate(lines, 1):
        print(f"{i:>{width}}  {line}")
    print()
