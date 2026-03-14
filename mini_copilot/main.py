#!/usr/bin/env python3
import json
import sys
import time
from pathlib import Path

try:
    import readline

    COMMANDS = ["/login", "/help", "/copy", "/model", "/search_provider", ".exit"]

    def completer(text, state):
        matches = [c for c in COMMANDS if c.startswith(text)]
        return matches[state] if state < len(matches) else None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
except ImportError:
    pass

from mini_copilot.github_api import chat, get_copilot_token, get_models
from mini_copilot.web_search import web_search

COMMANDS_HELP = [
    ("/login", "Authenticate with GitHub"),
    ("/help", "Show available commands"),
    ("/copy", "Copy last Copilot response to clipboard"),
    ("/model", "Select the model to use"),
    ("/search_provider", "Select the web search provider"),
    (".exit", "Quit"),
]

SEARCH_PROVIDERS = ["duckduckgo"]

CONFIG_PATH = Path.home() / ".config" / "mini-copilot" / "config.json"
TOKEN_REFRESH_INTERVAL = 24 * 60  # seconds

# Define the web search tool schema
WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for current, real-time, or recent information to help answer the user's question.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up on the web.",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of search results to return (default 20).",
                    "default": 20,
                },
            },
            "required": ["query"],
        },
    },
}

TOOLS = [WEB_SEARCH_TOOL]


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
    search_provider = "duckduckgo"

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
    current_model = "gpt-5.2"

    print("GitHub Copilot CLI ready. Available commands:")
    for cmd, desc in COMMANDS_HELP:
        print(f"  {cmd:<20} {desc}")
    print()

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
                print(f"  {cmd:<20} {desc}")
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
            try:
                model_data = get_models(copilot_token)
            except Exception as e:
                print(f"Error fetching models: {e}\n", file=sys.stderr)
                continue
            groups = {}
            for m in model_data:
                owner = m.get("owned_by", "unknown")
                groups.setdefault(owner, []).append(m["id"])
            flat_models = [m["id"] for m in model_data]
            print(f"\nCurrent model: {current_model}")
            print("Available models:")
            idx = 1
            model_index = {}
            for owner, ids in groups.items():
                print(f"  [{owner}]")
                for mid in ids:
                    marker = "*" if mid == current_model else " "
                    print(f"  {marker} {idx}. {mid}")
                    model_index[idx] = mid
                    idx += 1
            try:
                choice = input("Select model (number or name, Enter to keep current): ").strip()
                if choice:
                    if choice.isdigit():
                        n = int(choice)
                        if n in model_index:
                            current_model = model_index[n]
                            print(f"Model set to: {current_model}\n")
                        else:
                            print("Invalid selection.\n")
                    elif choice in flat_models:
                        current_model = choice
                        print(f"Model set to: {current_model}\n")
                    else:
                        print(f"Unknown model '{choice}'. Keeping {current_model}\n")
                else:
                    print()
            except (EOFError, KeyboardInterrupt):
                print()
            continue
        if user_input == "/search_provider":
            print(f"\nCurrent search provider: {search_provider}")
            print("Available providers:")
            for i, prov in enumerate(SEARCH_PROVIDERS, 1):
                marker = "*" if prov == search_provider else " "
                print(f"  {marker} {i}. {prov}")
            try:
                choice = input("Select search provider (number, Enter to keep current): ").strip()
                if choice:
                    if choice.isdigit():
                        n = int(choice)
                        if 1 <= n <= len(SEARCH_PROVIDERS):
                            search_provider = SEARCH_PROVIDERS[n - 1]
                            print(f"Search provider set to: {search_provider}\n")
                        else:
                            print("Invalid selection.\n")
                    else:
                        print("Please enter a number.\n")
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
            
            # First turn: get potential tool call
            response_message = chat(messages, copilot_token, current_model, tools=TOOLS)
            
            # Handle tool calls in a loop (for potentially multiple tools)
            while response_message.get("tool_calls"):
                messages.append(response_message)
                for tool_call in response_message["tool_calls"]:
                    function_name = tool_call["function"]["name"]
                    function_args = json.loads(tool_call["function"]["arguments"])
                    
                    if function_name == "web_search":
                        search_query = function_args.get("query")
                        num_results = function_args.get("num_results", 20)
                        
                        # In the future, search_provider can be passed to web_search()
                        search_context = web_search(search_query, num_results=num_results)
                        
                        messages.append({
                            "tool_call_id": tool_call["id"],
                            "role": "tool",
                            "name": function_name,
                            "content": search_context,
                        })
                
                # Turn after tool results: get the model's response based on context
                response_message = chat(messages, copilot_token, current_model, tools=TOOLS)

            reply = response_message["content"]
            messages.append({"role": "assistant", "content": reply})
            last_reply = reply

            print(f"\n{reply}\n")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
