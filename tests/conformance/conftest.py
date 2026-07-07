"""
Shared pytest fixtures for winebot-contracts conformance tests.

Run against either WineBot or WinBot:

    pytest tests/conformance/ -v \
      --api-url http://localhost:8000 \
      --api-token your-token-here

Auto-detects platform from /version response.
"""

import json
import os
import datetime
import socket
import subprocess
import sys

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
    parser.addoption(
        "--results-file",
        default=os.environ.get("CONFORMANCE_RESULTS_FILE", ""),
        help="Path to write structured JSON results for historical tracking",
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
        return


# ============================================================
# Results tracking — write structured JSON after each run
# ============================================================

def pytest_sessionfinish(session, exitstatus):
    """Write structured conformance results to --results-file (if specified)."""
    results_path = session.config.getoption("--results-file")
    if not results_path:
        return

    # Parse test outcomes from the terminalreporter's stats
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if not reporter:
        return

    stats = reporter.stats
    passed = len(stats.get("passed", []))
    failed = len(stats.get("failed", []))
    skipped = len(stats.get("skipped", []))
    xfailed = len(stats.get("xfailed", []))
    xpassed = len(stats.get("xpassed", []))
    errors = len(stats.get("errors", []))

    total = passed + failed + skipped + xfailed + xpassed + errors

    # Collect failure details
    failures = []
    for test in stats.get("failed", []):
        failures.append({
            "test": test.nodeid,
            "message": str(test.longrepr) if test.longrepr else "unknown",
        })

    # Detect git info
    git_sha = ""
    git_branch = ""
    try:
        git_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5
        ).stdout.strip()
        git_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5
        ).stdout.strip()
    except Exception:
        pass

    # Detect platform version from API
    api_version = ""
    platform_name = ""
    try:
        api_url = session.config.getoption("--api-url")
        token = session.config.getoption("--api-token")
        headers = {"X-API-Key": token} if token else {}
        r = requests.get(f"{api_url}/version", headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            api_version = data.get("api_version", "")
            platform_name = data.get("os", "")
    except Exception:
        pass

    result = {
        "run_id": datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S"),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "platform": {
            "name": platform_name or session.config.getoption("--api-url"),
            "api_version": api_version,
        },
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "xfailed": xfailed,
            "xpassed": xpassed,
            "errors": errors,
            "exit_code": exitstatus,
            "pass_rate": round(passed / total * 100, 1) if total > 0 else 0.0,
        },
        "environment": {
            "python_version": sys.version,
            "hostname": socket.gethostname(),
        },
        "git": {
            "sha": git_sha,
            "branch": git_branch,
        },
        "failures": failures,
    }

    os.makedirs(os.path.dirname(results_path) or ".", exist_ok=True)
    with open(results_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n[Conformance Results] Written to: {results_path}")
    print(f"[Conformance Results] {passed}/{total} passed ({result['summary']['pass_rate']}%)")
