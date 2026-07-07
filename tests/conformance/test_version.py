"""Version endpoint conformance tests (contract v1.0)."""

import pytest

pytestmark = pytest.mark.contract_v1


class TestVersion:
    """GET /version — API version info."""

    def test_version_returns_200(self, api):
        status, data = api("GET", "/version")
        assert status == 200

    def test_version_has_api_version(self, api):
        _, data = api("GET", "/version")
        assert "api_version" in data

    def test_version_is_semver(self, api):
        _, data = api("GET", "/version")
        parts = data["api_version"].split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_version_has_winbot_version(self, api):
        _, data = api("GET", "/version")
        assert "winbot_version" in data

    def test_version_has_os_field(self, api):
        _, data = api("GET", "/version")
        assert "os" in data
        assert data["os"] in ("Windows", "Linux", "wine")

    def test_version_has_hostname(self, api):
        _, data = api("GET", "/version")
        assert "hostname" in data
