import os

from iclaw import http

GITHUB_API_BASE = os.environ.get("ICLAW_GITHUB_API_BASE", "https://api.github.com")
COPILOT_API_BASE = os.environ.get(
    "ICLAW_COPILOT_API_BASE", "https://api.githubcopilot.com"
)

COPILOT_HEADERS = {
    "Content-Type": "application/json",
    "Editor-Version": "vscode/1.85.0",
    "Editor-Plugin-Version": "copilot/1.155.0",
    "User-Agent": "GithubCopilot/1.155.0",
    "Copilot-Integration-Id": "vscode-chat",
}


def get_copilot_token(github_token):
    resp = http.get_session().get(
        f"{GITHUB_API_BASE}/copilot_internal/v2/token",
        headers={
            "Authorization": f"Bearer {github_token}",
            "Editor-Version": "vscode/1.85.0",
            "Editor-Plugin-Version": "copilot/1.155.0",
            "User-Agent": "GithubCopilot/1.155.0",
        },
    )
    if not resp.ok:
        raise RuntimeError(
            f"Failed to get Copilot token: {resp.status_code} {resp.reason}"
        )
    return resp.json()["token"]


def get_models(copilot_token):
    resp = http.get_session().get(
        f"{COPILOT_API_BASE}/models",
        headers={"Authorization": f"Bearer {copilot_token}", **COPILOT_HEADERS},
    )
    if not resp.ok:
        raise RuntimeError(f"Failed to get models: {resp.status_code} {resp.reason}")
    return resp.json().get("data", [])


class UnsupportedModelError(Exception):
    pass


def chat(messages, copilot_token, model="gpt-4o", tools=None):
    payload = {"model": model, "messages": messages, "stream": False}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    resp = http.get_session().post(
        f"{COPILOT_API_BASE}/chat/completions",
        headers={"Authorization": f"Bearer {copilot_token}", **COPILOT_HEADERS},
        json=payload,
    )
    if not resp.ok:
        if resp.status_code == 400 and "unsupported_api_for_model" in resp.text:
            raise UnsupportedModelError(
                f'Model "{model}" is not accessible via /chat/completions'
            )
        raise RuntimeError(
            f"Chat API error: {resp.status_code} {resp.reason}\n{resp.text}"
        )
    return resp.json()["choices"][0]["message"]
