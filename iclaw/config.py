import json
import os
from pathlib import Path

_default_config = Path.home() / ".config" / "iclaw" / "config.json"
CONFIG_PATH = Path(os.environ.get("ICLAW_CONFIG_PATH", str(_default_config)))
TOKEN_REFRESH_INTERVAL = 24 * 60  # seconds


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text())
    except json.JSONDecodeError:
        return {}


def _save_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2))


def load_github_token():
    return _load_config().get("github_token")


def load_session_settings() -> dict:
    config = _load_config()
    return {
        "model_provider": config.get("model_provider", "copilot"),
        "current_model": config.get("current_model", "gpt-5.2"),
        "search_provider": config.get("search_provider", "duckduckgo"),
        "proxy": config.get("proxy"),
        "ca_bundle": config.get("ca_bundle"),
    }


def save_session_settings(
    *, model_provider, current_model, search_provider, proxy=None, ca_bundle=None
) -> None:
    config = _load_config()
    config["model_provider"] = model_provider
    config["current_model"] = current_model
    config["search_provider"] = search_provider
    config["proxy"] = proxy
    config["ca_bundle"] = ca_bundle
    _save_config(config)
