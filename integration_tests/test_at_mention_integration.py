"""Integration test for @ file mention (resolve_at_mentions).

Runs resolve_at_mentions in a subprocess to verify end-to-end file injection
without requiring a TTY or live API credentials.
"""

import subprocess
import sys
import os
import tempfile


def run_integration_test():
    print("Starting Integration Test for '@' file mention...")

    tmpdir = tempfile.mkdtemp()
    test_filename = os.path.join(tmpdir, "secret_phrase.txt")
    secret_content = "XYZZY_UNIQUE_SECRET_42"
    with open(test_filename, "w") as f:
        f.write(f"The magic word is: {secret_content}\n")

    script = f"""
import sys
sys.path.insert(0, {repr(os.getcwd())})
from iclaw.main import resolve_at_mentions

text = "What is written in @{test_filename}"
result = resolve_at_mentions(text)
print(result)
"""

    try:
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=15,
        )

        if proc.returncode != 0:
            print(f"Subprocess failed:\n{proc.stderr}")
            return False

        output = proc.stdout
        print(f"Output:\n{output}")

        # Verify file content was injected
        if secret_content not in output:
            print("FAILED: secret content not found in output.")
            return False

        if f'<file path="{test_filename}">' not in output:
            print("FAILED: <file> XML tag not found in output.")
            return False

        if "What is written in" not in output:
            print("FAILED: original message not preserved in output.")
            return False

        print("Integration Test PASSED!")
        return True

    finally:
        if os.path.exists(test_filename):
            os.remove(test_filename)
        if os.path.exists(tmpdir):
            os.rmdir(tmpdir)


def run_nonexistent_file_test():
    print("\nStarting test: nonexistent file mention returns original text...")

    script = f"""
import sys
sys.path.insert(0, {repr(os.getcwd())})
from iclaw.main import resolve_at_mentions

text = "look at @/nonexistent/path/file.txt"
result = resolve_at_mentions(text)
assert result == text, f"Expected original text, got: {{result!r}}"
print("OK")
"""

    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if proc.returncode == 0 and "OK" in proc.stdout:
        print("Nonexistent file test PASSED!")
        return True
    else:
        print(f"FAILED:\n{proc.stderr or proc.stdout}")
        return False


def run_multiple_files_test():
    print("\nStarting test: multiple @ mentions inject all files...")

    tmpdir = tempfile.mkdtemp()
    file1 = os.path.join(tmpdir, "foo.txt")
    file2 = os.path.join(tmpdir, "bar.txt")
    with open(file1, "w") as f:
        f.write("content of foo")
    with open(file2, "w") as f:
        f.write("content of bar")

    script = f"""
import sys
sys.path.insert(0, {repr(os.getcwd())})
from iclaw.main import resolve_at_mentions

text = "compare @{file1} and @{file2}"
result = resolve_at_mentions(text)
assert "content of foo" in result, "foo content missing"
assert "content of bar" in result, "bar content missing"
assert text in result, "original message missing"
print("OK")
"""

    try:
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode == 0 and "OK" in proc.stdout:
            print("Multiple files test PASSED!")
            return True
        else:
            print(f"FAILED:\n{proc.stderr or proc.stdout}")
            return False
    finally:
        for f in (file1, file2):
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists(tmpdir):
            os.rmdir(tmpdir)


if __name__ == "__main__":
    results = [
        run_integration_test(),
        run_nonexistent_file_test(),
        run_multiple_files_test(),
    ]
    if all(results):
        print("\nAll integration tests PASSED!")
        sys.exit(0)
    else:
        print("\nSome integration tests FAILED.")
        sys.exit(1)
