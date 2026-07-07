"""
Shared pytest fixtures for winebot-contracts conformance tests.

Run against either WineBot or WinBot:

    pytest tests/conformance/ -v \
      --api-url http://localhost:8000 \
      --api-token your-token-here

Auto-detects platform from /version response.
"""

import os
import pytest
import requests


def pytest_addoption(parser):
    parser.addoption(
        "--api-url",
        default=os.environ.get("API_URL", "http://127.0.0.1:8000"),
        help="Base URL of the target API (WineBot or WinBot)",
    )
    parser.addoption(
        "--api-token",
        default=os.environ.get("API_TOKEN", os.environ.get("WINBOT_API_TOKEN", "")),
        help="API token for authentication",
    )


@pytest.fixture(scope="session")
def api_url(request):
    """Base URL of the target API."""
    return request.config.getoption("--api-url").rstrip("/")


@pytest.fixture(scope="session")
def api_token(request):
    """API token for authentication."""
    return request.config.getoption("--api-token")


@pytest.fixture(scope="session")
def auth_headers(api_token):
    """HTTP headers with API authentication."""
    if not api_token:
        return {}
    return {"X-API-Key": api_token}


@pytest.fixture(scope="session")
def session(api_url, auth_headers):
    """Requests session with pre-configured auth."""
    s = requests.Session()
    s.headers.update(auth_headers)
    s.headers["Content-Type"] = "application/json"
    return s


@pytest.fixture(scope="session")
def platform(api_url, auth_headers):
    """Detect platform: 'winbot' or 'winebot'. Cached for the session."""
    try:
        r = requests.get(f"{api_url}/version", headers=auth_headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("os", "").lower() == "windows":
                return "winbot"
            return "winebot"
    except Exception:
        pass
    try:
        r = requests.get(f"{api_url}/health", headers=auth_headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if "x11" in str(data).lower() or "wine" in str(data).lower():
                return "winebot"
            return "winbot"
    except Exception:
        pass
    return "unknown"


@pytest.fixture(scope="session")
def api(api_url, session):
    """Make an authenticated request to the API.

    Usage: status, data = api("GET", "/health")
    """
    def _api(method: str, path: str, **kwargs):
        url = f"{api_url}{path}"
        kwargs.setdefault("timeout", 10)
        try:
            resp = session.request(method, url, **kwargs)
            try:
                return resp.status_code, resp.json()
            except (ValueError, requests.exceptions.JSONDecodeError):
                return resp.status_code, resp.text
        except requests.RequestException as e:
            return 0, {"error": str(e)}
    return _api


# ============================================================
# Markers
# ============================================================

def pytest_configure(config):
    config.addinivalue_line("markers", "winbot: test applies only to WinBot")
    config.addinivalue_line("markers", "winebot: test applies only to WineBot")
    config.addinivalue_line("markers", "contract_v1: test covers a v1.0 contract requirement")


def pytest_collection_modifyitems(config, items):
    """Apply platform-specific skipping."""
    if not any("--api-url" in arg for arg in config.invocation_params.args):
        return  # No target specified, don't skip
    # Platform is detected at runtime; tests that use platform fixture handle their own skipping
