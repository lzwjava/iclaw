import os
import subprocess

from prompt_toolkit.completion import Completer, Completion

COMMANDS = [
    "/provider_model",
    "/model",
    "/search",
    "/provider_search",
    "/proxy",
    "/ca_bundle",
    "/copy",
    "/status",
    "/help",
    ".exit",
]


def _get_git_files():
    """Return files from git ls-files, natively respecting .gitignore."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.splitlines()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return []


class IclawCompleter(Completer):
    """Handles both / command completion and @ file mention completion."""

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # @ file mention: find the last @ not followed by a space
        at_pos = text.rfind("@")
        if at_pos != -1:
            prefix = text[at_pos + 1 :]
            if " " not in prefix:
                all_files = _get_git_files()
                matches = [f for f in all_files if prefix.lower() in f.lower()]
                count = 0
                for path in sorted(matches):
                    if count >= 20:
                        break
                    count += 1
                    meta = "dir" if os.path.isdir(path) else "file"
                    yield Completion(
                        path,
                        start_position=-len(prefix),
                        display=path,
                        display_meta=meta,
                    )
                return

        # / command completion at start of input
        stripped = text.lstrip()
        if stripped.startswith("/") or stripped == ".":
            for cmd in COMMANDS:
                if cmd.startswith(stripped):
                    yield Completion(
                        cmd,
                        start_position=-len(stripped),
                        display=cmd,
                    )
