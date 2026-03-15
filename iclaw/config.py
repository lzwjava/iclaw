import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "iclaw" / "config.json"
TOKEN_REFRESH_INTERVAL = 24 * 60  # seconds


def load_github_token():
    if not CONFIG_PATH.exists():
        return None
    try:
        config = json.loads(CONFIG_PATH.read_text())
        return config.get("github_token")
    except json.JSONDecodeError:
        return None
