#!/usr/bin/env python3
import json
import sys
import time
from pathlib import Path

try:
    import readline

    COMMANDS = ["/login", "/help", "/copy", "/model", ".exit"]

    def completer(text, state):
        matches = [c for c in COMMANDS if c.startswith(text)]
        return matches[state] if state < len(matches) else None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
except ImportError:
    pass

from mini_copilot.github_api import chat, get_copilot_token

COMMANDS_HELP = [
    ("/login", "Authenticate with GitHub"),
    ("/help", "Show available commands"),
    ("/copy", "Copy last Copilot response to clipboard"),
    ("/model", "Select the model to use"),
    (".exit", "Quit"),
]

AVAILABLE_MODELS = [
    "gpt-4o",
    "gpt-4",
    "gpt-3.5-turbo",
    "o1-preview",
    "o1-mini",
    "claude-3.5-sonnet",
]

CONFIG_PATH = Path.home() / ".config" / "mini-copilot" / "config.json"
TOKEN_REFRESH_INTERVAL = 24 * 60  # seconds (~24 minutes)


def load_github_token():
    if not CONFIG_PATH.exists():
        return None
    config = json.loads(CONFIG_PATH.read_text())
    return config.get("github_token") or None


def run_login():
    from datetime import datetime, timezone

    from mini_copilot.login import get_device_code, poll_for_access_token

    try:
        device_data = get_device_code()
        github_token = poll_for_access_token(
            device_data["device_code"], device_data.get("interval", 5)
        )
        config = {
            "github_token": github_token,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(config, indent=2))
        print(f"\nSaved GitHub token to {CONFIG_PATH}")
        return github_token
    except Exception as e:
        print(f"\nLogin error: {e}", file=sys.stderr)
        return None


def copy_to_clipboard(text):
    import pyperclip

    pyperclip.copy(text)


def main():
    github_token = load_github_token()
    copilot_token = None
    token_expiry = 0
    last_reply = None

    if github_token:
        print("Connecting to GitHub Copilot...")
        try:
            copilot_token = get_copilot_token(github_token)
            token_expiry = time.monotonic() + TOKEN_REFRESH_INTERVAL
        except Exception as e:
            print(f"Warning: {e}", file=sys.stderr)
    else:
        print("No token found. Type /login to authenticate.\n")

    messages = []
    current_model = "gpt-4o"

    print(
        "GitHub Copilot CLI ready. Type your message, /login to authenticate, or .exit to quit.\n"
    )

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input in ("/", "/help"):
            print("\nAvailable commands:")
            for cmd, desc in COMMANDS_HELP:
                print(f"  {cmd:<10} {desc}")
            print()
            continue
        if user_input == ".exit":
            print("Goodbye!")
            break
        if user_input == "/copy":
            if last_reply:
                try:
                    copy_to_clipboard(last_reply)
                    print("Copied to clipboard.\n")
                except Exception as e:
                    print(f"Error copying to clipboard: {e}", file=sys.stderr)
            else:
                print("Nothing to copy yet.\n")
            continue
        if user_input == "/model":
            print(f"\nCurrent model: {current_model}")
            print("Available models:")
            for i, m in enumerate(AVAILABLE_MODELS):
                marker = "*" if m == current_model else " "
                print(f"  {marker} {i + 1}. {m}")
            try:
                choice = input(
                    "Select model (number or name, Enter to keep current): "
                ).strip()
                if choice:
                    if choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(AVAILABLE_MODELS):
                            current_model = AVAILABLE_MODELS[idx]
                            print(f"Model set to: {current_model}\n")
                        else:
                            print("Invalid selection.\n")
                    elif choice in AVAILABLE_MODELS:
                        current_model = choice
                        print(f"Model set to: {current_model}\n")
                    else:
                        print(f"Unknown model '{choice}'. Keeping {current_model}\n")
                else:
                    print()
            except (EOFError, KeyboardInterrupt):
                print()
            continue
        if user_input == "/login":
            github_token = run_login()
            if github_token:
                try:
                    copilot_token = get_copilot_token(github_token)
                    token_expiry = time.monotonic() + TOKEN_REFRESH_INTERVAL
                    print("Connected to GitHub Copilot.\n")
                except Exception as e:
                    print(f"Error: {e}", file=sys.stderr)
            continue

        if not copilot_token:
            print("Not authenticated. Type /login first.", file=sys.stderr)
            continue

        try:
            if time.monotonic() >= token_expiry:
                copilot_token = get_copilot_token(github_token)
                token_expiry = time.monotonic() + TOKEN_REFRESH_INTERVAL

            messages.append({"role": "user", "content": user_input})
            reply = chat(messages, copilot_token, current_model)
            messages.append({"role": "assistant", "content": reply})
            last_reply = reply

            print(f"\nGitHub Copilot: {reply}\n")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
