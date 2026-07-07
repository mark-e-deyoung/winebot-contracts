"""Lifecycle endpoint conformance tests (contract v1.0)."""

import pytest

pytestmark = pytest.mark.contract_v1


class TestLifecycleStatus:
    """GET /lifecycle/status — check for pending lifecycle actions."""

    def test_status_returns_200(self, api):
        status, data = api("GET", "/lifecycle/status")
        assert status == 200

    def test_status_has_required_fields(self, api):
        _, data = api("GET", "/lifecycle/status")
        assert "status" in data
        assert data["status"] in ("idle", "pending")
        assert "pending_action" in data
        assert "remaining_seconds" in data

    def test_status_idle_by_default(self, api):
        _, data = api("GET", "/lifecycle/status")
        if data["status"] == "idle":
            assert data["pending_action"] is None


class TestLifecycleShutdown:
    """POST /lifecycle/shutdown — initiate shutdown with cancel window."""

    def test_shutdown_returns_200(self, api):
        status, data = api("POST", "/lifecycle/shutdown")
        assert status == 200

    def test_shutdown_has_required_fields(self, api):
        _, data = api("POST", "/lifecycle/shutdown")
        assert data["status"] == "shutting_down"
        assert "delay_seconds" in data
        assert data["delay_seconds"] >= 10
        assert "cancel_before" in data
        assert data["cancel_command"] == "POST /lifecycle/cancel"
        assert "human_present" in data

    def test_shutdown_with_custom_delay(self, api):
        status, data = api("POST", "/lifecycle/shutdown?delay=10")
        assert status == 200
        assert data["delay_seconds"] == 10

    def test_shutdown_invalid_delay_rejected(self, api):
        status, data = api("POST", "/lifecycle/shutdown?delay=-1")
        assert status == 422, f"Expected 422 for invalid delay, got {status}"

    def test_shutdown_too_large_delay_rejected(self, api):
        status, data = api("POST", "/lifecycle/shutdown?delay=9999")
        assert status == 422, f"Expected 422 for oversized delay, got {status}"


class TestLifecycleRestart:
    """POST /lifecycle/restart — initiate restart with cancel window."""

    def test_restart_returns_200(self, api):
        status, data = api("POST", "/lifecycle/restart")
        assert status == 200

    def test_restart_has_required_fields(self, api):
        _, data = api("POST", "/lifecycle/restart")
        assert data["status"] == "restarting"
        assert "delay_seconds" in data
        assert data["delay_seconds"] >= 10


class TestLifecycleCancel:
    """POST /lifecycle/cancel — cancel pending shutdown/restart."""

    def test_cancel_without_pending(self, api):
        """Cancel with nothing pending returns no_pending, not an error."""
        # First clear any pending action
        api("POST", "/lifecycle/cancel")
        status, data = api("POST", "/lifecycle/cancel")
        assert status == 200
        assert data["status"] == "no_pending"

    def test_cancel_aborts_pending_shutdown(self, api):
        """Cancel called after shutdown returns cancelled."""
        api("POST", "/lifecycle/shutdown?delay=300")
        status, data = api("POST", "/lifecycle/cancel")
        assert status == 200
        assert data["status"] == "cancelled"
