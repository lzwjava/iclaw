import os

from iclaw import http
from iclaw.github_api import UnsupportedModelError

OPENROUTER_API_BASE = os.environ.get(
    "ICLAW_OPENROUTER_API_BASE", "https://openrouter.ai/api/v1"
)

_HEADERS = {
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/lzwjava/iclaw",
    "X-Title": "iclaw",
}


def _auth_headers(api_key):
    return {"Authorization": f"Bearer {api_key}", **_HEADERS}


def get_models(api_key):
    resp = http.get_session().get(
        f"{OPENROUTER_API_BASE}/models",
        headers=_auth_headers(api_key),
    )
    if not resp.ok:
        raise RuntimeError(f"Failed to get models: {resp.status_code} {resp.reason}")
    return resp.json().get("data", [])


def _parse_sse(resp):
    """Parse SSE stream from chat completions API, yielding content chunks."""
    for line in resp.iter_lines():
        if not line:
            continue
        line = line.decode("utf-8") if isinstance(line, bytes) else line
        if not line.startswith("data: "):
            continue
        data = line[6:]
        if data == "[DONE]":
            break
        try:
            import json

            chunk = json.loads(data)
            delta = chunk.get("choices", [{}])[0].get("delta", {})
            content = delta.get("content")
            if content:
                yield content
        except (ValueError, KeyError, IndexError):
            continue


def chat(messages, api_key, model, tools=None, stream=False):
    payload = {"model": model, "messages": messages, "stream": stream}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    resp = http.get_session().post(
        f"{OPENROUTER_API_BASE}/chat/completions",
        headers=_auth_headers(api_key),
        json=payload,
        stream=stream,
    )
    if not resp.ok:
        if resp.status_code == 404:
            raise UnsupportedModelError(f'Model "{model}" not found on OpenRouter')
        raise RuntimeError(
            f"Chat API error: {resp.status_code} {resp.reason}\n{resp.text}"
        )
    if stream:
        return _parse_sse(resp)
    return resp.json()["choices"][0]["message"]
