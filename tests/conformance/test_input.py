"""Input endpoint conformance tests (contract v1.0).

Canonical paths (both implementations MUST support):
  POST /input/mouse/click
  POST /input/key

WinBot additionally provides:
  POST /input/mouse/move
  POST /input/keyboard/type
  POST /input/keyboard/press
"""

import pytest

pytestmark = pytest.mark.contract_v1


class TestMouseClick:
    """POST /input/mouse/click — click at screen coordinates."""

    def test_click_accepts_valid_coordinates(self, api):
        status, data = api("POST", "/input/mouse/click", json={"x": 100, "y": 200})
        # Runtime may fail if no display is available, but should not be a validation error
        assert status not in (422,), f"Validation rejected valid input: {data}"
        assert status in (200, 201, 202, 400, 403, 500), f"Unexpected status: {status}"

    def test_click_rejects_missing_coordinates(self, api):
        status, data = api("POST", "/input/mouse/click", json={})
        assert status == 422, f"Expected 422 for missing coordinates, got {status}"


class TestKeyboardInput:
    """POST /input/key — type text or key combinations.

    Canonical path: POST /input/key
    WinBot also supports: POST /input/keyboard/press, POST /input/keyboard/type
    """

    @pytest.mark.winbot
    def test_canonical_path_on_winbot(self, api, platform):
        """WinBot should alias /input/key to its keyboard implementation."""
        if platform != "winbot":
            pytest.skip("WinBot-specific")
        status, data = api("POST", "/input/key", json={"keys": "test"})
        assert status not in (404,), f"Canonical path /input/key returned 404 on WinBot"
        assert status in (200, 400, 422, 500)

    @pytest.mark.winebot
    def test_canonical_path_on_winebot(self, api, platform):
        """WineBot should respond to /input/key natively."""
        if platform != "winebot":
            pytest.skip("WineBot-specific")
        status, data = api("POST", "/input/key", json={"keys": "test"})
        assert status in (200, 400, 422, 500)


class TestMouseMove:
    """POST /input/mouse/move — WinBot-specific; may not exist on WineBot."""

    def test_mouse_move_rejects_empty_body(self, api):
        status, data = api("POST", "/input/mouse/move", json={})
        assert status == 422, f"Expected 422 for empty move, got {status}"
