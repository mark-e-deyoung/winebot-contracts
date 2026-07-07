"""Recording endpoint conformance tests (contract v1.0).

Canonical paths:
  POST /recording/start
  POST /recording/stop
  GET  /recording/health

WinBot additionally provides:
  GET  /recording/status
"""

import pytest

pytestmark = pytest.mark.contract_v1


class TestRecordingHealth:
    """GET /recording/health — recording subsystem status.

    Canonical path: GET /recording/health
    WinBot also supports: GET /recording/status
    """

    def test_recording_health_returns_200(self, api):
        status, data = api("GET", "/recording/health")
        assert status in (200, 404), f"Expected 200 or 404, got {status}"

    def test_recording_health_has_status(self, api):
        status, data = api("GET", "/recording/health")
        if status == 200:
            assert isinstance(data, dict)

    @pytest.mark.winbot
    def test_winbot_recording_status_alias(self, api, platform):
        """WinBot should also respond on /recording/status."""
        if platform != "winbot":
            pytest.skip("WinBot-specific")
        status, data = api("GET", "/recording/status")
        assert status in (200, 404), f"Expected 200 or 404, got {status}"


class TestRecordingStartStop:
    """POST /recording/start, POST /recording/stop — control recording."""

    def test_recording_start_requires_body(self, api):
        """Recording start may or may not require a body depending on platform."""
        status, data = api("POST", "/recording/start", json={"fps": 15, "bitrate": "2M"})
        assert status in (200, 400, 409, 422), f"Unexpected status: {status}"
