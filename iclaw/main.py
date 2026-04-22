#!/usr/bin/env python3
import json
import os
import sys
import time

from prompt_toolkit import PromptSession

from iclaw import http
from iclaw import log
from iclaw.at_mention import resolve_at_mentions
from iclaw.commands.compact import handle_compact_command
from iclaw.commands.export import handle_export_command
from iclaw.commands.log import handle_log_command
from iclaw.commands.model import handle_model_command, handle_model_provider_command
from iclaw.commands.proxy import handle_ca_bundle_command, handle_proxy_command
from iclaw.commands.read import handle_read_command
from iclaw.commands.search_provider import handle_search_provider_command
from iclaw.commands.utils import handle_copy_command
from iclaw.completer import IclawCompleter
from iclaw.config import (
    CONFIG_PATH,
    TOKEN_REFRESH_INTERVAL,
    load_github_token,
    load_openrouter_api_key,
    load_session_settings,
    save_session_settings,
)
from iclaw.exec_tool import exec_command as exec
from iclaw.github_api import UnsupportedModelError, chat, get_copilot_token
from iclaw.providers import openrouter
from iclaw.tools.defs import TOOLS
from iclaw.tools.edit_tool import EditTool
from iclaw.web_search import web_search

COMMANDS_HELP = [
    ("/provider_model", "Select and authenticate with the model provider"),
    ("/model", "Select specific model from your provider"),
    ("/search", "Web search (usage: /search <query>)"),
    ("/provider_search", "Select the web search provider"),
    ("/proxy", "Set HTTP/HTTPS proxy (usage: /proxy [url|off])"),
    ("/ca_bundle", "Set CA bundle for HTTPS (usage: /ca_bundle [path|off])"),
    ("/log", "Set log verbosity (usage: /log [verbose|info])"),
    ("/copy", "Copy last Copilot response to clipboard"),
    ("/read", "Print file contents to terminal (usage: /read <path>)"),
    ("/clear", "Clear conversation history"),
    ("/compact", "Compact conversation history using LLM"),
    ("/export", "Export full conversation history to JSON file"),
    ("/status", "Show current settings"),
    ("/help", "Show available commands"),
    ("/exit", "Quit"),
]


def _chat(provider, token, messages, model, tools=None):
    if provider == "openrouter":
        return openrouter.chat(messages, token, model, tools=tools)
    return chat(messages, token, model, tools=tools)


def main():
    github_token = load_github_token()
    provider_token = None
    token_expiry = 0
    last_reply = None
    settings = load_session_settings()
    model_provider = settings["model_provider"]
    current_model = settings["current_model"]
    search_provider = settings["search_provider"]
    proxy = settings["proxy"]
    ca_bundle = settings["ca_bundle"]
    log_level = settings["log_level"]
    log.set_level(
        {"info": log.INFO, "verbose": log.VERBOSE}.get(log_level, log.VERBOSE)
    )
    http.reconfigure(proxy=proxy, ca_bundle=ca_bundle)

    if model_provider == "copilot" and github_token:
        log.log_info("Connecting to GitHub Copilot...")
        try:
            provider_token = get_copilot_token(github_token)
            token_expiry = time.monotonic() + TOKEN_REFRESH_INTERVAL
        except Exception as e:
            print(f"Warning: {e}", file=sys.stderr)
    elif model_provider == "openrouter":
        provider_token = load_openrouter_api_key()
        if provider_token:
            log.log_info("Using OpenRouter.")
        else:
            log.log_info(
                "OpenRouter selected but no API key found. Type /provider_model.\n"
            )
    else:
        log.log_info("No token found. Type /provider_model to authenticate.\n")

    print(
        """
  ██  █████  ██       █████  ██   ██
  ██ ██      ██      ██   ██ ██   ██
  ██ ██      ██      ███████ ██ █ ██
  ██ ██      ██      ██   ██ ██████
  ██  █████  ███████ ██   ██  ███ ██
"""
    )

    messages = []
    tool_logs = []
    log.log_info("Available commands:")
    for cmd, desc in COMMANDS_HELP:
        log.log_info(f"  {cmd:<20} {desc}")
    log.log_info("")

    session = PromptSession(completer=IclawCompleter(), complete_while_typing=True)

    while True:
        try:
            user_input = session.prompt("> ").strip()
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
        if user_input in ("/exit", ".exit"):
            print("Goodbye!")
            break
        if user_input == "/copy":
            handle_copy_command(last_reply)
            continue
        if user_input == "/read" or user_input.startswith("/read "):
            parts = user_input.split(maxsplit=1)
            arg = parts[1] if len(parts) > 1 else None
            handle_read_command(arg)
            continue
        if user_input.startswith("@") and not any(c.isspace() for c in user_input):
            handle_read_command(user_input)
            continue
        if user_input == "/provider_model":
            p, t = handle_model_provider_command(CONFIG_PATH, model_provider)
            if t:
                model_provider = p
                provider_token = t
                if model_provider == "copilot":
                    github_token = load_github_token()
                    token_expiry = time.monotonic() + TOKEN_REFRESH_INTERVAL
                else:
                    token_expiry = 0
                save_session_settings(
                    model_provider=model_provider,
                    current_model=current_model,
                    search_provider=search_provider,
                    proxy=proxy,
                    ca_bundle=ca_bundle,
                    log_level=log_level,
                )
            continue
        if user_input == "/model":
            current_model = handle_model_command(
                model_provider, provider_token, current_model
            )
            save_session_settings(
                model_provider=model_provider,
                current_model=current_model,
                search_provider=search_provider,
                proxy=proxy,
                ca_bundle=ca_bundle,
                log_level=log_level,
            )
            continue
        if user_input.startswith("/search") or user_input == "/search":
            if user_input.startswith("/search "):
                query = user_input.split(maxsplit=1)[1]
            else:
                # Use last user message as query
                last_user_msg = next(
                    (m["content"] for m in reversed(messages) if m["role"] == "user"),
                    None,
                )
                if not last_user_msg:
                    print(
                        "No previous message to search. Usage: /search <query>",
                        file=sys.stderr,
                    )
                    continue
                query = last_user_msg
            search_context = web_search(query, num_results=5, provider=search_provider)
            if not provider_token:
                log.log_info(f"\n{search_context}\n")
                continue
            search_msg = (
                f"Based on the following web search results for '{query}', "
                "provide a concise and helpful answer.\n\n"
                f"{search_context}"
            )
            messages.append({"role": "user", "content": search_msg})
            try:
                if (
                    model_provider == "copilot"
                    and time.monotonic() >= token_expiry
                    and github_token
                ):
                    provider_token = get_copilot_token(github_token)
                    token_expiry = time.monotonic() + TOKEN_REFRESH_INTERVAL
                response_message = _chat(
                    model_provider, provider_token, messages, current_model, tools=TOOLS
                )
                reply = response_message.get("content", "")
                messages.append({"role": "assistant", "content": reply})
                last_reply = reply
                log.log_info(f"\n{reply}\n")
            except UnsupportedModelError as e:
                print(f"Error: {e}", file=sys.stderr)
                print("Please select a different model with /model", file=sys.stderr)
                messages.pop()
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
            continue
        if user_input == "/provider_search":
            search_provider = handle_search_provider_command(search_provider)
            save_session_settings(
                model_provider=model_provider,
                current_model=current_model,
                search_provider=search_provider,
                proxy=proxy,
                ca_bundle=ca_bundle,
                log_level=log_level,
            )
            continue
        if user_input == "/proxy" or user_input.startswith("/proxy "):
            parts = user_input.split(maxsplit=1)
            arg = parts[1] if len(parts) > 1 else None
            proxy = handle_proxy_command(proxy, arg)
            http.reconfigure(proxy=proxy, ca_bundle=ca_bundle)
            save_session_settings(
                model_provider=model_provider,
                current_model=current_model,
                search_provider=search_provider,
                proxy=proxy,
                ca_bundle=ca_bundle,
                log_level=log_level,
            )
            continue
        if user_input == "/ca_bundle" or user_input.startswith("/ca_bundle "):
            parts = user_input.split(maxsplit=1)
            arg = parts[1] if len(parts) > 1 else None
            ca_bundle = handle_ca_bundle_command(ca_bundle, arg)
            http.reconfigure(proxy=proxy, ca_bundle=ca_bundle)
            save_session_settings(
                model_provider=model_provider,
                current_model=current_model,
                search_provider=search_provider,
                proxy=proxy,
                ca_bundle=ca_bundle,
                log_level=log_level,
            )
            continue
        if user_input == "/log" or user_input.startswith("/log "):
            parts = user_input.split(maxsplit=1)
            arg = parts[1] if len(parts) > 1 else None
            handle_log_command(arg)
            if arg in ("verbose", "info"):
                log_level = arg
                save_session_settings(
                    model_provider=model_provider,
                    current_model=current_model,
                    search_provider=search_provider,
                    proxy=proxy,
                    ca_bundle=ca_bundle,
                    log_level=log_level,
                )
            continue
        if user_input == "/status":
            print(f"  model_provider:  {model_provider}")
            print(f"  model:           {current_model}")
            print(f"  search_provider: {search_provider}")
            print(f"  proxy:           {proxy or '(not set)'}")
            print(f"  ca_bundle:       {ca_bundle or '(system default)'}")
            print(f"  log_level:       {log_level}")
            print(f"  cwd:             {os.getcwd()}")
            print()
            continue
        if user_input == "/clear":
            messages.clear()
            tool_logs.clear()
            last_reply = None
            print("Conversation history cleared.")
            continue
        if user_input == "/compact":
            messages = handle_compact_command(
                messages,
                lambda m, t, mdl, tools=None: _chat(
                    model_provider, t, m, mdl, tools=tools
                ),
                provider_token,
                current_model,
            )
            continue
        if user_input == "/export":
            handle_export_command(messages, tool_logs)
            continue

        if not provider_token:
            print("Not authenticated. Type /provider_model first.", file=sys.stderr)
            continue

        try:
            if (
                model_provider == "copilot"
                and time.monotonic() >= token_expiry
                and github_token
            ):
                provider_token = get_copilot_token(github_token)
                token_expiry = time.monotonic() + TOKEN_REFRESH_INTERVAL

            messages.append(
                {"role": "user", "content": resolve_at_mentions(user_input)}
            )
            response_message = _chat(
                model_provider, provider_token, messages, current_model, tools=TOOLS
            )

            while response_message.get("tool_calls"):
                messages.append(response_message)
                for tool_call in response_message["tool_calls"]:
                    function_name = tool_call["function"]["name"]
                    function_args = json.loads(tool_call["function"]["arguments"])
                    log.log_verbose(
                        f"[tool] Calling {function_name} with {json.dumps(function_args)}"
                    )

                    if function_name == "web_search":
                        search_context = web_search(
                            function_args.get("query"),
                            num_results=function_args.get("num_results", 20),
                            provider=search_provider,
                        )
                        tool_logs.append(
                            {
                                "timestamp": time.time(),
                                "function": function_name,
                                "args": function_args,
                                "result": search_context[:500] + "..."
                                if len(search_context) > 500
                                else search_context,
                            }
                        )
                        messages.append(
                            {
                                "tool_call_id": tool_call["id"],
                                "role": "tool",
                                "name": function_name,
                                "content": search_context,
                            }
                        )
                        log.log_verbose(f"[tool] Result: ({len(search_context)} chars)")

                    if function_name == "exec":
                        output = exec(function_args.get("command"))
                        tool_logs.append(
                            {
                                "timestamp": time.time(),
                                "function": function_name,
                                "args": function_args,
                                "result": output[:500] + "..."
                                if len(output) > 500
                                else output,
                            }
                        )
                        messages.append(
                            {
                                "tool_call_id": tool_call["id"],
                                "role": "tool",
                                "name": function_name,
                                "content": output,
                            }
                        )
                        log.log_verbose(f"[tool] Result: {output[:500]}")

                    if function_name == "edit":
                        file_path = function_args.get("file_path")
                        result = EditTool.edit(
                            file_path, function_args.get("edit_content")
                        )
                        with open(file_path, "w") as f:
                            f.write(result)
                        tool_logs.append(
                            {
                                "timestamp": time.time(),
                                "function": function_name,
                                "args": function_args,
                                "result": f"Successfully edited {file_path}",
                            }
                        )
                        messages.append(
                            {
                                "tool_call_id": tool_call["id"],
                                "role": "tool",
                                "name": function_name,
                                "content": f"Successfully edited {file_path}",
                            }
                        )
                        log.log_verbose(
                            f"[tool] Result: Successfully edited {file_path}"
                        )

                response_message = _chat(
                    model_provider, provider_token, messages, current_model, tools=TOOLS
                )

            reply = response_message["content"]
            messages.append({"role": "assistant", "content": reply})
            last_reply = reply
            log.log_info(f"\n{reply}\n")
        except UnsupportedModelError as e:
            print(f"Error: {e}", file=sys.stderr)
            print("Please select a different model with /model", file=sys.stderr)
            messages.pop()
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
