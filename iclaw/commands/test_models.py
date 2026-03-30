from iclaw import http
from iclaw.github_api import COPILOT_API_BASE, COPILOT_HEADERS


def test_model(copilot_token, model_id):
    """Test if a model works with /chat/completions"""
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "hi"}],
        "stream": False,
    }
    try:
        resp = http.get_session().post(
            f"{COPILOT_API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {copilot_token}", **COPILOT_HEADERS},
            json=payload,
            timeout=10,
        )
        return model_id, resp.status_code == 200
    except Exception:
        return model_id, False
