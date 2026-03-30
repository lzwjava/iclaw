#!/usr/bin/env python3
import json
import os
import sys
import time

from prompt_toolkit import PromptSession

from iclaw import http
from iclaw import log
from iclaw.at_mention import resolve_at_mentions
from iclaw.commands.log import handle_log_command
from iclaw.commands.model import handle_model_command, handle_model_provider_command
from iclaw.commands.proxy import handle_ca_bundle_command, handle_proxy_command
from iclaw.commands.search_provider import handle_search_provider_command
from iclaw.commands.utils import handle_copy_command
from iclaw.completer import IclawCompleter
from iclaw.config import (
    CONFIG_PATH,
    TOKEN_REFRESH_INTERVAL,
    load_github_token,
    load_session_settings,
    save_session_settings,
)
from iclaw.exec_tool import exec_command as exec
from iclaw.github_api import chat, get_copilot_token
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
    ("/clear", "Clear conversation history"),
    ("/status", "Show current settings"),
    ("/help", "Show available commands"),
    (".exit", "Quit"),
]


def main():
    github_token = load_github_token()
    copilot_token = None
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

    if github_token:
        log.log_info("Connecting to GitHub Copilot...")
        try:
            copilot_token = get_copilot_token(github_token)
            token_expiry = time.monotonic() + TOKEN_REFRESH_INTERVAL
        except Exception as e:
            print(f"Warning: {e}", file=sys.stderr)
    else:
        log.log_info("No token found. Type /provider_model to authenticate.\n")

    messages = []
    log.log_info("iclaw CLI ready. Available commands:")
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
        if user_input == ".exit":
            print("Goodbye!")
            break
        if user_input == "/copy":
            handle_copy_command(last_reply)
            continue
        if user_input == "/provider_model":
            p, t = handle_model_provider_command(CONFIG_PATH, model_provider)
            if t:
                model_provider = p
                copilot_token = t
                github_token = load_github_token()
                token_expiry = time.monotonic() + TOKEN_REFRESH_INTERVAL
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
            current_model = handle_model_command(copilot_token, current_model)
            save_session_settings(
                model_provider=model_provider,
                current_model=current_model,
                search_provider=search_provider,
                proxy=proxy,
                ca_bundle=ca_bundle,
                log_level=log_level,
            )
            continue
        if user_input.startswith("/search "):
            query = user_input.split(maxsplit=1)[1]
            search_context = web_search(query, num_results=5, provider=search_provider)
            if not copilot_token:
                log.log_info(f"\n{search_context}\n")
                continue
            search_msg = (
                f"Based on the following web search results for '{query}', "
                "provide a concise and helpful answer.\n\n"
                f"{search_context}"
            )
            messages.append({"role": "user", "content": search_msg})
            try:
                if time.monotonic() >= token_expiry and github_token:
                    copilot_token = get_copilot_token(github_token)
                    token_expiry = time.monotonic() + TOKEN_REFRESH_INTERVAL
                response_message = chat(
                    messages, copilot_token, current_model, tools=TOOLS
                )
                reply = response_message.get("content", "")
                messages.append({"role": "assistant", "content": reply})
                last_reply = reply
                log.log_info(f"\n{reply}\n")
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
            last_reply = None
            print("Conversation history cleared.")
            continue

        if not copilot_token:
            print("Not authenticated. Type /provider_model first.", file=sys.stderr)
            continue

        try:
            if time.monotonic() >= token_expiry and github_token:
                copilot_token = get_copilot_token(github_token)
                token_expiry = time.monotonic() + TOKEN_REFRESH_INTERVAL

            messages.append(
                {"role": "user", "content": resolve_at_mentions(user_input)}
            )
            response_message = chat(messages, copilot_token, current_model, tools=TOOLS)

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

                response_message = chat(
                    messages, copilot_token, current_model, tools=TOOLS
                )

            reply = response_message["content"]
            messages.append({"role": "assistant", "content": reply})
            last_reply = reply
            log.log_info(f"\n{reply}\n")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
