import requests

from iclaw.config import load_session_settings

_session = None


def get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        _session.trust_env = False
        settings = load_session_settings()
        reconfigure(proxy=settings.get("proxy"), ca_bundle=settings.get("ca_bundle"))
    return _session


def reconfigure(proxy=None, ca_bundle=None):
    s = get_session()
    if proxy:
        s.proxies = {"http": proxy, "https": proxy}
    else:
        s.proxies = {}
    if ca_bundle:
        s.verify = ca_bundle
    else:
        s.verify = True
