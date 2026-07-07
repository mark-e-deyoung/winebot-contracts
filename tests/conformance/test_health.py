"""Health endpoint conformance tests (contract v1.0)."""

import pytest

pytestmark = pytest.mark.contract_v1


class TestHealth:
    """GET /health — top-level health summary."""

    def test_health_returns_200(self, api):
        status, data = api("GET", "/health")
        assert status == 200, f"Expected 200, got {status}"

    def test_health_has_status_field(self, api):
        _, data = api("GET", "/health")
        assert "status" in data, "Response missing 'status' field"
        assert data["status"] in ("ok", "degraded"), (
            f"Expected 'ok' or 'degraded', got '{data.get('status')}'"
        )

    def test_health_has_hostname(self, api):
        _, data = api("GET", "/health")
        assert "hostname" in data

    def test_health_has_tools_section(self, api):
        _, data = api("GET", "/health")
        assert "tools" in data, "Response missing 'tools' field"

    def test_health_has_storage_section(self, api):
        _, data = api("GET", "/health")
        assert "storage" in data, "Response missing 'storage' field"


class TestHealthSystem:
    """GET /health/system — system resource info."""

    def test_system_health_returns_200(self, api):
        status, data = api("GET", "/health/system")
        assert status in (200, 404), f"Expected 200 or 404, got {status}"

    @pytest.mark.skip(reason="GPU detection not yet implemented on all platforms")
    def test_system_has_gpu_field(self, api):
        status, data = api("GET", "/health/system")
        if status == 200:
            assert "gpu_available" in data, (
                "WinBot should report gpu_available:true (native GPU); "
                "WineBot: gpu_available:false (Xvfb)"
            )

    def test_system_has_cpu_info(self, api):
        status, data = api("GET", "/health/system")
        if status == 200:
            assert "cpu_count" in data
            assert "memory" in data


class TestHealthTools:
    """GET /health/tools — installed tool status."""

    def test_tools_returns_200(self, api):
        status, data = api("GET", "/health/tools")
        assert status == 200

    def test_tools_has_tools_field(self, api):
        _, data = api("GET", "/health/tools")
        assert "tools" in data

    def test_tools_has_all_ok(self, api):
        _, data = api("GET", "/health/tools")
        assert "all_ok" in data

    @pytest.mark.winbot
    def test_winbot_has_python_tool(self, api, platform):
        if platform != "winbot":
            pytest.skip("WinBot-specific")
        _, data = api("GET", "/health/tools")
        tools = data.get("tools", {})
        assert "python" in tools, "Python tool status missing"


class TestHealthPresence:
    """GET /health/presence — human presence detection."""

    def test_presence_returns_200(self, api):
        status, data = api("GET", "/health/presence")
        assert status == 200

    def test_presence_has_required_fields(self, api):
        _, data = api("GET", "/health/presence")
        assert "present" in data
        assert isinstance(data["present"], bool)
        assert "evidence" in data
        assert isinstance(data["evidence"], list)
