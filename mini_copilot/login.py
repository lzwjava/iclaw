#!/usr/bin/env python3
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

CONFIG_PATH = Path.home() / ".config" / "mini-copilot" / "config.json"
GITHUB_CLIENT_ID = "01ab8ac9400c4e429b23"  # VSCode's client ID


def get_device_code():
    resp = requests.post(
        "https://github.com/login/device/code",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json={"client_id": GITHUB_CLIENT_ID, "scope": "read:user repo"},
    )
    resp.raise_for_status()
    data = resp.json()
    print(f"\n➡️  Visit: {data['verification_uri']}")
    print(f"➡️  Enter code: {data['user_code']}\n")
    return data


def poll_for_access_token(device_code, interval=5):
    while True:
        time.sleep(interval)
        resp = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json={
                "client_id": GITHUB_CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
        )
        resp.raise_for_status()
        data = resp.json()

        if "access_token" in data:
            print("✅ GitHub OAuth token obtained.")
            return data["access_token"]
        elif data.get("error") == "authorization_pending":
            print("⏳ Waiting for user authorization...", end="\r")
        elif data.get("error") == "slow_down":
            interval += 5
        elif data.get("error") == "expired_token":
            raise RuntimeError("Device code expired. Please restart.")
        else:
            raise RuntimeError(f"OAuth error: {json.dumps(data)}")


def main():
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
        print(f"\n✅ Saved GitHub token to {CONFIG_PATH}")
        print("🚀 Now you can run 'mini-copilot' to start chatting.")
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
