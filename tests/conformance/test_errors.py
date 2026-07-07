"""Error handling conformance tests (contract v1.0)."""

import pytest

pytestmark = pytest.mark.contract_v1


class TestErrorResponses:
    """Verify error responses conform to the contract."""

    def test_404_on_unknown_endpoint(self, api):
        """GET /nonexistent must return 404."""
        status, data = api("GET", "/nonexistent")
        assert status == 404, f"Expected 404 for unknown endpoint, got {status}"

    def test_404_has_detail_field(self, api):
        """404 responses must have a 'detail' field."""
        _, data = api("GET", "/nonexistent")
        assert "detail" in data, "404 response missing 'detail' field"

    def test_401_without_token(self, api_url):
        """Requests without X-API-Key must return 401."""
        import requests
        resp = requests.get(f"{api_url}/health", timeout=10)
        assert resp.status_code == 401, (
            f"Expected 401 without auth, got {resp.status_code}"
        )

    def test_401_has_detail_field(self, api_url):
        """401 responses must have a 'detail' field."""
        import requests
        resp = requests.get(f"{api_url}/health", timeout=10)
        try:
            data = resp.json()
            assert "detail" in data
        except (ValueError, TypeError):
            pytest.fail("401 response is not valid JSON")

    def test_422_on_validation_error(self, api):
        """POST endpoints with missing required fields should return 422."""
        status, data = api("POST", "/input/mouse/click", json={})
        assert status == 422, f"Expected 422 for missing fields, got {status}"

    def test_422_has_detail_field(self, api):
        """422 responses must have a 'detail' field."""
        _, data = api("POST", "/input/mouse/click", json={})
        assert "detail" in data, "422 response missing 'detail' field"
