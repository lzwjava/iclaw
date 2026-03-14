import subprocess
import time
import sys
import os


def run_integration_test():
    print("🚀 Starting Integration Test for 'edit' tool...")

    # Ensure current directory is in PYTHONPATH for the subprocess
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd() + ":" + env.get("PYTHONPATH", "")

    # Create a test file
    test_filename = "test_edit_integration.txt"
    with open(test_filename, "w") as f:
        f.write("Line 1\nLine 2\nLine 3\n")

    # Start the iclaw process
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
                print("✅ Prompt detected.")
                break

        if "> " not in output:
            print(f"❌ Timed out waiting for prompt. Last output: {output}")
            return False

        # 2. Trigger tool
        print(f"Sending message to trigger 'edit' tool on {test_filename}...")
        edit_request = f"Edit the file {test_filename}. Change 'Line 2' to 'Line Two'.\n"
        process.stdin.write(edit_request)
        process.stdin.flush()

        # 3. Look for tool execution
        print("Monitoring for tool invocation and response...")
        found_tool = False
        found_success = False
        start_time = time.time()
        output = ""
        while time.time() - start_time < 60:
            char = process.stdout.read(1)
            if not char:
                break
            output += char
            sys.stdout.write(char)
            sys.stdout.flush()

            if f"Successfully edited {test_filename}" in output:
                found_tool = True
                
            # If the assistant replies and we found the tool message, we are good
            if found_tool and "> " in output:
                found_success = True
                break

        if found_tool:
            # Verify file content
            with open(test_filename, "r") as f:
                content = f.read()
            if "Line Two" in content and "Line 2" not in content:
                print(f"\n✅ File content verified: {test_filename}")
                print("\n🎉 Integration Test PASSED!")
                return True
            else:
                print(f"\n❌ File content mismatch. Content: {content}")
                return False
        else:
            print("\n❌ Integration Test FAILED (Tool not triggered or response not found).")
            return False

    finally:
        process.terminate()
        if os.path.exists(test_filename):
            os.remove(test_filename)


if __name__ == "__main__":
    if run_integration_test():
        sys.exit(0)
    else:
        sys.exit(1)
