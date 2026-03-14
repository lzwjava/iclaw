import json
import sys
from datetime import datetime, timezone
from iclaw.login import get_device_code, poll_for_access_token


def handle_login_command(config_path):
    print("\nSelect authentication method for Copilot:")
    print("  1. Standard Login (Device Code Flow)")
    print("  2. Direct GITHUB_AUTH_TOKEN")

    choice = input("Choice (1 or 2): ").strip()

    github_token = None
    if choice == "1":
        try:
            device_data = get_device_code()
            github_token = poll_for_access_token(
                device_data["device_code"], device_data.get("interval", 5)
            )
        except Exception as e:
            print(f"\nLogin error: {e}", file=sys.stderr)
            return None
    elif choice == "2":
        github_token = input("Enter your GITHUB_AUTH_TOKEN: ").strip()
        if not github_token:
            print("Token cannot be empty.")
            return None
    else:
        print("Invalid selection.")
        return None

    if github_token:
        config = {
            "github_token": github_token,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config, indent=2))
        print(f"\nSaved GitHub token to {config_path}")
        return github_token

    return None
