"""Automation endpoint conformance tests (contract v1.0).

Canonical paths:
  GET  /screenshot
  GET  /windows
  POST /apps/run
  POST /inspect/window
"""

import pytest

pytestmark = pytest.mark.contract_v1


class TestScreenshot:
    """GET /screenshot — capture desktop screenshot."""

    def test_screenshot_returns_200_or_acceptable(self, api):
        status, data = api("GET", "/screenshot")
        assert status in (200, 400, 409, 429, 503), f"Unexpected status: {status}"

    def test_screenshot_is_image_when_successful(self, api, api_url, session):
        """When screenshot succeeds, response must be an image."""
        resp = session.get(f"{api_url}/screenshot", timeout=10)
        if resp.status_code == 200:
            content_type = resp.headers.get("content-type", "")
            assert content_type.startswith("image/"), (
                f"Expected image content-type, got {content_type}"
            )
            assert "x-screenshot-path" in resp.headers, (
                "Missing x-screenshot-path header"
            )


class TestWindows:
    """GET /windows — list visible windows."""

    def test_windows_returns_200(self, api):
        status, data = api("GET", "/windows")
        assert status == 200

    def test_windows_has_count(self, api):
        _, data = api("GET", "/windows")
        assert "count" in data
        assert isinstance(data["count"], int)

    def test_windows_has_list(self, api):
        _, data = api("GET", "/windows")
        assert "windows" in data
        assert isinstance(data["windows"], list)


class TestWindowFocus:
    """POST /windows/focus — focus a window by title."""

    def test_focus_nonexistent_window(self, api):
        status, data = api("POST", "/windows/focus", json={
            "title": "zzz_nonexistent_window_xyzzy"
        })
        assert status == 200
        assert "status" in data

    def test_focus_empty_title(self, api):
        """Empty title should return a status, not crash."""
        status, data = api("POST", "/windows/focus", json={"title": ""})
        assert status == 200


class TestInspectWindow:
    """POST /inspect/window — inspect window details."""

    def test_inspect_returns_200(self, api):
        status, data = api("POST", "/inspect/window", json={})
        assert status == 200
        assert "status" in data


class TestAppRun:
    """POST /apps/run — launch a Windows application."""

    def test_app_run_missing_path(self, api):
        status, data = api("POST", "/apps/run", json={})
        assert status == 422, f"Expected 422 for missing path, got {status}"

    def test_app_run_with_valid_path(self, api):
        status, data = api("POST", "/apps/run", json={
            "path": "cmd.exe",
            "args": "/c echo hello",
            "detach": False
        })
        assert status in (200, 404, 403), f"Unexpected status: {status}"
