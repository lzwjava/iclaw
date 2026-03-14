import subprocess
import time
import sys
import os


def run_integration_test():
    print("🚀 Starting Integration Test for 'exec' tool...")

    # Ensure current directory is in PYTHONPATH for the subprocess
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd() + ":" + env.get("PYTHONPATH", "")

    # Start the leanclaw process
    process = subprocess.Popen(
        [sys.executable, "-m", "leanclaw.main"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Combine stdout and stderr
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
        print("Sending message to trigger 'exec' tool...")
        process.stdin.write("run command: echo integration_test_success\n")
        process.stdin.flush()

        # 3. Look for tool execution
        print("Monitoring for tool invocation and response...")
        found_tool = False
        found_output = False
        start_time = time.time()
        output = ""
        while time.time() - start_time < 60:
            char = process.stdout.read(1)
            if not char:
                break
            output += char
            sys.stdout.write(char)  # Echo for observability
            sys.stdout.flush()

            if "[exec] Running command: echo integration_test_success" in output:
                found_tool = True

            if "integration_test_success" in output and found_tool:
                found_output = True
                print("\n✅ Found expected output in responses!")
                break

        if found_output:
            print("\n🎉 Integration Test PASSED!")
            return True
        else:
            print("\n❌ Integration Test FAILED.")
            return False

    finally:
        process.terminate()


if __name__ == "__main__":
    if run_integration_test():
        sys.exit(0)
    else:
        sys.exit(1)
