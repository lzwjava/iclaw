import json
import sys
from datetime import datetime, timezone
from iclaw.login import get_device_code, poll_for_access_token

def handle_login_command(config_path, token_refresh_interval):
    try:
        device_data = get_device_code()
        github_token = poll_for_access_token(
            device_data["device_code"], device_data.get("interval", 5)
        )
        config = {
            "github_token": github_token,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config, indent=2))
        print(f"\nSaved GitHub token to {config_path}")
        return github_token
    except Exception as e:
        print(f"\nLogin error: {e}", file=sys.stderr)
        return None
