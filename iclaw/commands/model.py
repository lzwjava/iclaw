import sys
import concurrent.futures
from iclaw.github_api import get_models, get_copilot_token
from iclaw.providers import openrouter
from iclaw.commands.auth import handle_login_command
from iclaw.commands.test_models import test_model
from iclaw.config import load_openrouter_api_key, save_openrouter_api_key


def _prompt_openrouter_key():
    env_key = load_openrouter_api_key()
    if env_key:
        print("Using OPENROUTER_API_KEY from environment.\n")
        return env_key
    key = input("Enter OpenRouter API key (stored in config): ").strip()
    if not key:
        print("API key cannot be empty.\n")
        return None
    save_openrouter_api_key(key)
    return key


def handle_model_provider_command(config_path, current_provider):
    PROVIDERS = ["copilot", "openrouter"]
    print(f"\nCurrent model provider: {current_provider}")
    print("Available model providers:")
    for i, p in enumerate(PROVIDERS, 1):
        marker = "*" if p == current_provider else " "
        print(f"  {marker} {i}. {p}")

    choice = input("Select model provider (number, Enter to keep current): ").strip()
    if not choice:
        return current_provider, None

    if not choice.isdigit():
        print("Invalid selection.\n")
        return current_provider, None

    n = int(choice)
    if not (1 <= n <= len(PROVIDERS)):
        print("Invalid selection.\n")
        return current_provider, None

    provider = PROVIDERS[n - 1]
    if provider == "copilot":
        github_token = handle_login_command(config_path)
        if not github_token:
            return current_provider, None
        try:
            token = get_copilot_token(github_token)
            print("Connected to GitHub Copilot.\n")
            return provider, token
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return current_provider, None

    if provider == "openrouter":
        key = _prompt_openrouter_key()
        if not key:
            return current_provider, None
        print("OpenRouter configured.\n")
        return provider, key

    return current_provider, None


def _handle_copilot_model(copilot_token, current_model):
    try:
        model_data = get_models(copilot_token)
    except Exception as e:
        print(f"Error fetching models: {e}\n", file=sys.stderr)
        return current_model

    total = len(model_data)
    print(f"Testing {total} models...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(test_model, copilot_token, m["id"]): m for m in model_data
        }
        working_models = []
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            _model_id, works = future.result()
            if works:
                working_models.append(futures[future])
            completed += 1
            pct = int(completed * 100 / total)
            print(f"\r{pct}% ({completed}/{total})", end="", flush=True)
    print()

    return _select_from_models(working_models, current_model, group_key="owned_by")


def _handle_openrouter_model(api_key, current_model):
    try:
        model_data = openrouter.get_models(api_key)
    except Exception as e:
        print(f"Error fetching models: {e}\n", file=sys.stderr)
        return current_model
    return _select_from_models(model_data, current_model, group_key=None)


def _select_from_models(models, current_model, group_key):
    if not models:
        print("No models available.\n")
        return current_model

    flat_ids = [m["id"] for m in models]
    print(f"\nCurrent model: {current_model}")
    print("Available models:")

    idx = 1
    model_index = {}

    if group_key:
        groups = {}
        for m in models:
            groups.setdefault(m.get(group_key, "unknown"), []).append(m["id"])
        for owner, ids in groups.items():
            print(f"  [{owner}]")
            for mid in ids:
                marker = "*" if mid == current_model else " "
                print(f"  {marker} {idx}. {mid}")
                model_index[idx] = mid
                idx += 1
    else:
        for mid in flat_ids:
            marker = "*" if mid == current_model else " "
            print(f"  {marker} {idx}. {mid}")
            model_index[idx] = mid
            idx += 1

    try:
        choice = input("Select model (number or name, Enter to keep current): ").strip()
        if not choice:
            return current_model
        if choice.isdigit():
            n = int(choice)
            if n in model_index:
                print(f"Model set to: {model_index[n]}\n")
                return model_index[n]
            print("Invalid selection.\n")
            return current_model
        if choice in flat_ids:
            print(f"Model set to: {choice}\n")
            return choice
        print(f"Unknown model '{choice}'. Keeping {current_model}\n")
    except (EOFError, KeyboardInterrupt):
        print()
    return current_model


def handle_model_command(provider_or_token, token_or_model, current_model=None):
    """Dispatch model selection by provider.

    Two call styles are accepted:
      handle_model_command(provider, token, current_model)  — new, preferred
      handle_model_command(copilot_token, current_model)    — legacy Copilot-only
    """
    if current_model is None:
        copilot_token, current_model = provider_or_token, token_or_model
        provider, token = "copilot", copilot_token
    else:
        provider, token = provider_or_token, token_or_model

    if not token:
        print("Not authenticated with any model provider.\n", file=sys.stderr)
        return current_model
    if provider == "copilot":
        return _handle_copilot_model(token, current_model)
    if provider == "openrouter":
        return _handle_openrouter_model(token, current_model)
    print(f"Unknown provider: {provider}\n", file=sys.stderr)
    return current_model
