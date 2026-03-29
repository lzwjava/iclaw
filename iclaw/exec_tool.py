import subprocess

from iclaw.log import log_verbose


def exec_command(command: str) -> str:
    """Execute a shell command and return its output (stdout or stderr)."""
    log_verbose(f"[exec] Running command: {command}")
    try:
        # Run command with a 30s timeout, capturing both stdout and stderr
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = result.stdout if result.returncode == 0 else result.stderr
        if not output.strip():
            output = f"(Process exited with code {result.returncode})"
        return output
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        print(exec_command(" ".join(sys.argv[1:])))
