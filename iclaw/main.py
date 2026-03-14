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

from iclaw.github_api import chat, get_copilot_token
from iclaw.web_search import web_search
from iclaw.exec_tool import exec_command as exec
from tools.edit_tool import EditTool
from iclaw.commands.auth import handle_login_command
from iclaw.commands.model import handle_model_command
from iclaw.commands.search_provider import handle_search_provider_command
from iclaw.commands.utils import handle_copy_command

COMMANDS_HELP = [
    ("/login", "Authenticate with GitHub"),
    ("/help", "Show available commands"),
    ("/copy", "Copy last Copilot response to clipboard"),
    ("/model", "Select the model to use"),
    ("/search_provider", "Select the web search provider"),
    (".exit", "Quit"),
]

CONFIG_PATH = Path.home() / ".config" / "iclaw" / "config.json"
TOKEN_REFRESH_INTERVAL = 24 * 60  # seconds

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

EXEC_COMMAND_TOOL = {
    "type": "function",
    "function": {
        "name": "exec",
        "description": "Execute a shell command on the local system and return the output.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute.",
                },
            },
            "required": ["command"],
        },
    },
}

EDIT_TOOL = {
    "type": "function",
    "function": {
        "name": "edit",
        "description": "Apply a unified diff edit to a file on the local system.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the file to edit.",
                },
                "edit_content": {
                    "type": "string",
                    "description": "The unified diff content to apply.",
                },
            },
            "required": ["file_path", "edit_content"],
        },
    },
}
TOOLS = [WEB_SEARCH_TOOL, EXEC_COMMAND_TOOL, EDIT_TOOL]


def load_github_token():
    if not CONFIG_PATH.exists():
        return None
    config = json.loads(CONFIG_PATH.read_text())
    return config.get("github_token")


def main():
    github_token = load_github_token()
    copilot_token = None
    token_expiry = 0
    last_reply = None
    search_provider = "duckduckgo"
    current_model = "gpt-5.2"

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
            handle_copy_command(last_reply)
            continue
        if user_input == "/model":
            current_model = handle_model_command(copilot_token, current_model)
            continue
        if user_input == "/search_provider":
            search_provider = handle_search_provider_command(search_provider)
            continue
        if user_input == "/login":
            github_token = handle_login_command(CONFIG_PATH, TOKEN_REFRESH_INTERVAL)
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
            response_message = chat(messages, copilot_token, current_model, tools=TOOLS)

            while response_message.get("tool_calls"):
                messages.append(response_message)
                for tool_call in response_message["tool_calls"]:
                    function_name = tool_call["function"]["name"]
                    function_args = json.loads(tool_call["function"]["arguments"])

                    if function_name == "web_search":
                        search_query = function_args.get("query")
                        num_results = function_args.get("num_results", 20)

                        search_context = web_search(
                            search_query,
                            num_results=num_results,
                            provider=search_provider,
                        )

                        messages.append(
                            {
                                "tool_call_id": tool_call["id"],
                                "role": "tool",
                                "name": function_name,
                                "content": search_context,
                            }
                        )

                    if function_name == "exec":
                        command = function_args.get("command")
                        output = exec(command)

                        messages.append(
                            {
                                "tool_call_id": tool_call["id"],
                                "role": "tool",
                                "name": function_name,
                                "content": output,
                            }
                        )

                    if function_name == "edit":
                        file_path = function_args.get("file_path")
                        edit_content = function_args.get("edit_content")

                        result = EditTool.edit(file_path, edit_content)
                        with open(file_path, "w") as f:
                            f.write(result)

                        messages.append(
                            {
                                "tool_call_id": tool_call["id"],
                                "role": "tool",
                                "name": function_name,
                                "content": f"Successfully edited {file_path}",
                            }
                        )
                response_message = chat(
                    messages, copilot_token, current_model, tools=TOOLS
                )

            reply = response_message["content"]
            messages.append({"role": "assistant", "content": reply})
            last_reply = reply
            print(f"\n{reply}\n")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
