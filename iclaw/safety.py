"""Safety level enforcement for exec and edit tools.

Levels:
  low  — no restrictions (default)
  high — file mutations (edit/write/delete/move) restricted to CWD;
         read-only commands and global tools (pip, python, etc.) still work.
"""

import os
import re
import shlex


def _is_within(target: str, root: str) -> bool:
    """Return True if target path is inside root (or equals root)."""
    try:
        target_real = os.path.realpath(os.path.expanduser(target))
        root_real = os.path.realpath(root)
        return target_real == root_real or target_real.startswith(root_real + os.sep)
    except (ValueError, OSError):
        return False


def _resolve_path_maybe(path: str) -> str:
    """Best-effort resolve a path token to an absolute path."""
    expanded = os.path.expanduser(path)
    if not os.path.isabs(expanded):
        expanded = os.path.join(os.getcwd(), expanded)
    return expanded


# ── Dangerous patterns for "high" safety ──────────────────────────────────────

# Commands that DELETE files outside CWD
_DELETE_RE = re.compile(
    r"^\s*(?:sudo\s+)?(?:rm|rmdir)\s+",
    re.IGNORECASE,
)

# Commands that MOVE/RENAME files — check destination
_MOVE_RE = re.compile(
    r"^\s*(?:sudo\s+)?mv\s+",
    re.IGNORECASE,
)

# Commands that COPY files — check destination
_COPY_RE = re.compile(
    r"^\s*(?:sudo\s+)?cp\s+",
    re.IGNORECASE,
)

# Commands that WRITE/CREATE files via redirect
_REDIRECT_RE = re.compile(
    r"[>]",  # any > or >>
)

# Commands that are always allowed (read-only / package managers / compilers)
_ALWAYS_ALLOWED_PREFIXES = (
    "pip",
    "pip3",
    "python",
    "python3",
    "node",
    "npm",
    "npx",
    "yarn",
    "cargo",
    "rustc",
    "go ",
    "java",
    "javac",
    "gcc",
    "g++",
    "clang",
    "make",
    "cmake",
    "docker",
    "git",
    "curl",
    "wget",
    "ssh",
    "scp",
    "cat",
    "head",
    "tail",
    "less",
    "more",
    "grep",
    "rg",
    "find",
    "ls",
    "tree",
    "file",
    "stat",
    "wc",
    "diff",
    "sort",
    "uniq",
    "echo",
    "printf",
    "date",
    "env",
    "which",
    "whereis",
    "whoami",
    "ps",
    "top",
    "htop",
    "df",
    "du",
    "free",
    "uname",
    "id",
    "tar",
    "zip",
    "unzip",
    "gzip",
    "gunzip",
    "pytest",
    "unittest",
    "tox",
    "ruff",
    "black",
    "isort",
    "mypy",
    "pyright",
    "flake8",
    "coverage",
    "bandit",
    "brew",
    "apt",
    "apt-get",
    "yum",
    "dnf",
    "pacman",
    "curl",
    "wget",
    "ping",
    "dig",
    "nslookup",
    "traceroute",
    "tmux",
    "screen",
    "less",
    "man",
    "info",
    "help",
    "cd",
    "pwd",
    "pushd",
    "popd",
    "source",
    "export",
    "set",
)


def _has_redirect_to_file_outside_cwd(command: str, cwd: str) -> bool:
    """Check if command redirects output (>) to a file outside CWD."""
    if not _REDIRECT_RE.search(command):
        return False
    # Split on > or >> and check what follows
    parts = re.split(r">+>", command)
    if len(parts) < 2:
        parts = re.split(r">", command)
    for part in parts[1:]:
        token = part.strip().split()[0] if part.strip() else ""
        if token and token != "/dev/null":
            resolved = _resolve_path_maybe(token)
            if not _is_within(resolved, cwd):
                return True
    return False


def _extract_path_args(args: list[str], count: int = -1) -> list[str]:
    """Extract path-like arguments, skipping flags."""
    paths = []
    i = 0
    while i < len(args):
        if args[i].startswith("-"):
            # flags with values: -t /path, --target=/path
            if "=" in args[i]:
                i += 1
                continue
            # flags that take a value argument
            if args[i] in ("-t", "--target", "-d", "--directory", "-C"):
                i += 2
                continue
            i += 1
            continue
        paths.append(args[i])
        if count > 0 and len(paths) >= count:
            break
        i += 1
    return paths


def check_exec_safety(command: str, safety_level: str) -> str | None:
    """Check if a command is allowed under the given safety level.

    Returns None if allowed, or an error message string if blocked.
    """
    if safety_level != "high":
        return None

    cwd = os.getcwd()

    # Always-allowed commands (read-only, package managers, etc.)
    try:
        tokens = shlex.split(command)
    except ValueError:
        # Malformed shell command — let it through, shell will handle it
        return None
    if not tokens:
        return None

    cmd_base = os.path.basename(tokens[0])

    if cmd_base in _ALWAYS_ALLOWED_PREFIXES or any(
        cmd_base.startswith(p) for p in _ALWAYS_ALLOWED_PREFIXES
    ):
        # Even allowed commands: still block redirects to outside CWD
        if _has_redirect_to_file_outside_cwd(command, cwd):
            return f"Safety HIGH: redirect to file outside CWD is blocked. CWD={cwd}"
        return None

    # rm / rmdir: block if target is outside CWD
    if _DELETE_RE.match(command):
        paths = _extract_path_args(tokens[1:])
        for p in paths:
            resolved = _resolve_path_maybe(p)
            if not _is_within(resolved, cwd):
                return (
                    f"Safety HIGH: cannot delete outside CWD. "
                    f"Blocked: {p} (resolved: {resolved}), CWD={cwd}"
                )
        return None

    # mv: block if either source or dest is outside CWD
    if _MOVE_RE.match(command):
        paths = _extract_path_args(tokens[1:])
        for p in paths:
            resolved = _resolve_path_maybe(p)
            if not _is_within(resolved, cwd):
                return (
                    f"Safety HIGH: cannot move files outside CWD. "
                    f"Blocked: {p} (resolved: {resolved}), CWD={cwd}"
                )
        return None

    # cp: block if destination is outside CWD
    if _COPY_RE.match(command):
        paths = _extract_path_args(tokens[1:])
        if len(paths) >= 2:
            dest = _resolve_path_maybe(paths[-1])
            if not _is_within(dest, cwd):
                return (
                    f"Safety HIGH: cannot copy to outside CWD. "
                    f"Blocked dest: {paths[-1]} (resolved: {dest}), CWD={cwd}"
                )
        return None

    # Redirect to file outside CWD
    if _has_redirect_to_file_outside_cwd(command, cwd):
        return f"Safety HIGH: redirect to file outside CWD is blocked. CWD={cwd}"

    # Default: allow (covers unknown commands that aren't destructive by name)
    return None


def check_edit_safety(file_path: str, safety_level: str) -> str | None:
    """Check if editing a file is allowed under the given safety level.

    Returns None if allowed, or an error message string if blocked.
    """
    if safety_level != "high":
        return None

    cwd = os.getcwd()
    resolved = _resolve_path_maybe(file_path)
    if not _is_within(resolved, cwd):
        return (
            f"Safety HIGH: cannot edit file outside CWD. "
            f"Blocked: {file_path} (resolved: {resolved}), CWD={cwd}"
        )
    return None
