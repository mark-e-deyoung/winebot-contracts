"""HTTP header conformance tests (contract v1.0)."""

import pytest

pytestmark = pytest.mark.contract_v1


class TestResponseHeaders:
    """Verify response headers conform to the contract."""

    def test_request_id_header_present(self, api_url, auth_headers):
        """Every response must carry X-Request-ID header."""
        import requests
        resp = requests.get(f"{api_url}/health", headers=auth_headers, timeout=10)
        assert "x-request-id" in resp.headers, "Missing X-Request-ID header"

    def test_request_id_is_uuid_format(self, api_url, auth_headers):
        """X-Request-ID values must be UUID-formatted."""
        import requests
        resp = requests.get(f"{api_url}/health", headers=auth_headers, timeout=10)
        rid = resp.headers.get("x-request-id", "")
        assert len(rid) == 36, f"X-Request-ID has unexpected length: {len(rid)}"
        assert rid.count("-") == 4

    @pytest.mark.winbot
    def test_winbot_version_headers(self, api_url, auth_headers):
        """WinBot sends X-WinBot-Version headers on /health and /version."""
        import requests
        resp = requests.get(f"{api_url}/health", headers=auth_headers, timeout=10)
        assert "x-winbot-version" in resp.headers
        assert "x-winbot-api-version" in resp.headers

    def test_auth_header_accepted(self, api_url, auth_headers):
        """Correct X-API-Key header must be accepted."""
        import requests
        resp = requests.get(f"{api_url}/health", headers=auth_headers, timeout=10)
        assert resp.status_code == 200, (
            f"Auth header not accepted: {resp.status_code}"
        )

    def test_version_headers_not_on_run_endpoints(self, api_url, auth_headers):
        """Version headers must NOT leak on non-versioned endpoints."""
        import requests
        resp = requests.post(
            f"{api_url}/run/python",
            headers={**auth_headers, "Content-Type": "application/json"},
            json={"script": "print(1)"},
            timeout=10,
        )
        if resp.status_code == 200:
            assert "x-winbot-version" not in [k.lower() for k in resp.headers.keys()]
