import subprocess
import time
import sys
import os
import tempfile


def run_integration_test():
    print("Starting Integration Test for '@' file mention...")

    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd() + ":" + env.get("PYTHONPATH", "")

    # Create a temp file with distinctive content
    tmpdir = tempfile.mkdtemp()
    test_filename = os.path.join(tmpdir, "secret_phrase.txt")
    secret_content = "XYZZY_UNIQUE_SECRET_42"
    with open(test_filename, "w") as f:
        f.write(f"The magic word is: {secret_content}\n")

    process = subprocess.Popen(
        [sys.executable, "-m", "iclaw.main"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=os.getcwd(),
        env=env,
    )

    try:
        # 1. Wait for prompt
        print("Waiting for prompt...")
        output = ""
        start_time = time.time()
        while time.time() - start_time < 30:
            char = process.stdout.read(1)
            if not char:
                break
            output += char
            if "> " in output:
                print("Prompt detected.")
                break

        if "> " not in output:
            print(f"Timed out waiting for prompt. Last output: {output}")
            return False

        # 2. Send message with @ mention of the test file
        print(f"Sending message with @{test_filename}...")
        request = (
            f"What is written in @{test_filename} ? Just repeat the exact content.\n"
        )
        process.stdin.write(request)
        process.stdin.flush()

        # 3. Wait for the LLM response containing the secret phrase
        print("Monitoring for response containing file content...")
        found_content = False
        start_time = time.time()
        output = ""
        while time.time() - start_time < 60:
            char = process.stdout.read(1)
            if not char:
                break
            output += char
            sys.stdout.write(char)
            sys.stdout.flush()

            if secret_content in output:
                found_content = True

            # Wait for next prompt to confirm response is complete
            if found_content and output.endswith("> "):
                break

        if found_content:
            print(f"\nLLM response contained file content ({secret_content}).")
            print("\nIntegration Test PASSED!")
            return True
        else:
            print("\nIntegration Test FAILED (file content not found in response).")
            print(f"Output was:\n{output}")
            return False

    finally:
        process.terminate()
        if os.path.exists(test_filename):
            os.remove(test_filename)
        if os.path.exists(tmpdir):
            os.rmdir(tmpdir)


if __name__ == "__main__":
    if run_integration_test():
        sys.exit(0)
    else:
        sys.exit(1)
