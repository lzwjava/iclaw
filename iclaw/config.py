import json
import os
from pathlib import Path

_default_config = Path.home() / ".config" / "iclaw" / "config.json"
CONFIG_PATH = Path(os.environ.get("ICLAW_CONFIG_PATH", str(_default_config)))
TOKEN_REFRESH_INTERVAL = 24 * 60  # seconds


def load_github_token():
    if not CONFIG_PATH.exists():
        return None
    try:
        config = json.loads(CONFIG_PATH.read_text())
        return config.get("github_token")
    except json.JSONDecodeError:
        return None
