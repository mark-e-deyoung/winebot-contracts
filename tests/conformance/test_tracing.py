"""Input tracing endpoint conformance tests (contract v1.0).

Canonical paths:
  POST /input/trace/start
  POST /input/trace/stop
  GET  /input/trace/status
  GET  /input/events

WinBot additionally supports:
  GET  /input/trace/events
"""

import pytest

pytestmark = pytest.mark.contract_v1


class TestTraceStatus:
    """GET /input/trace/status — current tracing state."""

    def test_trace_status_returns_200(self, api):
        status, data = api("GET", "/input/trace/status")
        assert status == 200

    def test_trace_status_has_tracing_field(self, api):
        _, data = api("GET", "/input/trace/status")
        assert "tracing" in data
        assert isinstance(data["tracing"], bool)


class TestTraceEvents:
    """GET /input/events — query traced input events.

    Canonical path: GET /input/events
    WinBot additionally supports: GET /input/trace/events
    """

    def test_events_returns_200(self, api):
        status, data = api("GET", "/input/events")
        assert status == 200

    @pytest.mark.winbot
    def test_winbot_events_alias(self, api, platform):
        """WinBot should also respond on /input/trace/events."""
        if platform != "winbot":
            pytest.skip("WinBot-specific")
        status, data = api("GET", "/input/trace/events")
        assert status == 200


class TestTraceStartStop:
    """POST /input/trace/start, POST /input/trace/stop."""

    def test_trace_start_returns_200(self, api):
        status, data = api("POST", "/input/trace/start")
        assert status == 200

    def test_trace_stop_returns_200(self, api):
        status, data = api("POST", "/input/trace/stop")
        assert status == 200
