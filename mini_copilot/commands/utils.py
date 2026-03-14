import sys

def handle_copy_command(last_reply):
    if last_reply:
        try:
            import pyperclip
            pyperclip.copy(last_reply)
            print("Copied to clipboard.\n")
        except Exception as e:
            print(f"Error copying to clipboard: {e}", file=sys.stderr)
    else:
        print("Nothing to copy yet.\n")
