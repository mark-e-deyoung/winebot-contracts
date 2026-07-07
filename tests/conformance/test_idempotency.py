"""Idempotency / Operations endpoint conformance tests (contract v1.0).

Canonical paths:
  GET  /operations
  GET  /operations/{operation_id}
"""

import pytest

pytestmark = pytest.mark.contract_v1


class TestOperationsList:
    """GET /operations — list recent operations."""

    def test_operations_returns_200(self, api):
        status, data = api("GET", "/operations")
        assert status == 200

    def test_operations_returns_list_or_dict(self, api):
        _, data = api("GET", "/operations")
        assert isinstance(data, (list, dict))
        if isinstance(data, dict):
            # Should have an 'operations' key or be the list itself
            assert "operations" in data or len(data) > 0


class TestOperationsGet:
    """GET /operations/{operation_id} — get a specific operation."""

    def test_get_nonexistent_operation(self, api):
        status, data = api("GET", "/operations/nonexistent-op-12345")
        assert status == 404, f"Expected 404 for unknown operation, got {status}"
