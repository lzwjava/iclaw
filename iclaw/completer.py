import os
import subprocess

from prompt_toolkit.completion import Completer, Completion

COMMANDS = [
    "/cmd",
    "/provider_model",
    "/model",
    "/paste",
    "/search",
    "/provider_search",
    "/proxy",
    "/ca_bundle",
    "/log",
    "/copy",
    "/cd",
    "/read",
    "/safety",
    "/status",
    "/browse",
    "/help",
    "/clear",
    "/compact",
    "/export",
    "/exit",
]

# Common shell commands for /cmd completion
COMMON_SHELL_COMMANDS = [
    "cat",
    "cd",
    "chmod",
    "cp",
    "curl",
    "diff",
    "echo",
    "env",
    "find",
    "git",
    "grep",
    "head",
    "kill",
    "less",
    "ls",
    "make",
    "mkdir",
    "mv",
    "pip",
    "ps",
    "python",
    "python3",
    "rm",
    "rmdir",
    "sed",
    "sort",
    "ssh",
    "tail",
    "tar",
    "touch",
    "uname",
    "wc",
    "which",
    "whoami",
]


def _get_path_commands():
    """Discover commands from PATH for /cmd completion."""
    commands = set(COMMON_SHELL_COMMANDS)
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        try:
            for entry in os.scandir(directory):
                if entry.is_file() and os.access(entry.path, os.X_OK):
                    commands.add(entry.name)
        except (PermissionError, FileNotFoundError):
            pass
    return sorted(commands)


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

        # /cd directory completion
        stripped = text.lstrip()
        if stripped.startswith("/cd "):
            prefix = stripped[4:]
            expanded = os.path.expanduser(prefix)
            dirname = os.path.dirname(expanded) or "."
            basename = os.path.basename(expanded)
            try:
                entries = os.scandir(dirname)
                dirs = [
                    e.name
                    for e in entries
                    if e.is_dir() and e.name.startswith(basename)
                ]
            except (PermissionError, FileNotFoundError):
                dirs = []
            count = 0
            for d in sorted(dirs):
                if count >= 20:
                    break
                count += 1
                full = (
                    os.path.join(os.path.dirname(prefix), d)
                    if os.path.dirname(prefix)
                    else d
                )
                yield Completion(
                    full + "/",
                    start_position=-len(prefix),
                    display=d + "/",
                    display_meta="dir",
                )
            return

        # /cmd shell command completion
        if stripped.startswith("/cmd ") or stripped == "/cmd":
            parts = stripped.split(maxsplit=1)
            if len(parts) > 1:
                prefix = parts[1]
                commands = _get_path_commands()
                matches = [c for c in commands if c.startswith(prefix)]
                count = 0
                for cmd in sorted(matches):
                    if count >= 20:
                        break
                    count += 1
                    yield Completion(
                        cmd,
                        start_position=-len(prefix),
                        display=cmd,
                        display_meta="cmd",
                    )
            return

        # / command completion at start of input
        if stripped.startswith("/") or stripped == ".":
            for cmd in COMMANDS:
                if cmd.startswith(stripped):
                    yield Completion(
                        cmd,
                        start_position=-len(stripped),
                        display=cmd,
                    )
