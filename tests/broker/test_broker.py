"""Tests for the shared InputBroker control plane."""

import time
from unittest.mock import MagicMock

import pytest

from winebot_contracts.broker import (
    ControlMode,
    ControlPolicyMode,
    InputBroker,
    UserIntent,
)


@pytest.fixture
def broker():
    return InputBroker()


class TestControlPolicy:
    def test_default_state(self, broker):
        state = broker.get_state()
        assert state.control_mode == ControlMode.USER
        assert state.effective_control_mode == ControlPolicyMode.HYBRID
        assert state.agent_status.value == "IDLE"

    def test_human_only_blocks_agent(self, broker):
        broker.set_instance_control_mode(ControlPolicyMode.HUMAN_ONLY)
        assert broker.check_access() is False

    def test_agent_only_allows_agent(self, broker):
        broker.set_instance_control_mode(ControlPolicyMode.AGENT_ONLY)
        assert broker.check_access() is True

    def test_hybrid_allows_agent_in_non_interactive(self, broker):
        broker.update_session("sess-1", interactive=False)
        assert broker.check_access() is True

    def test_hybrid_blocks_agent_in_interactive_without_grant(self, broker):
        broker.update_session("sess-1", interactive=True)
        assert broker.check_access() is False


class TestAgentGrant:
    def test_grant_requires_challenge_token(self, broker):
        with pytest.raises(PermissionError, match="challenge token"):
            broker.grant_agent(300, user_ack=True, challenge_token="wrong")

    def test_grant_with_valid_challenge(self, broker):
        broker.update_session("sess-1", interactive=True)
        challenge = broker.issue_grant_challenge()
        broker.grant_agent(300, user_ack=True, challenge_token=challenge["token"])
        state = broker.get_state()
        assert state.control_mode == ControlMode.AGENT
        assert state.lease_expiry is not None

    def test_grant_without_user_ack_fails(self, broker):
        challenge = broker.issue_grant_challenge()
        with pytest.raises(PermissionError, match="acknowledgement"):
            broker.grant_agent(300, user_ack=False, challenge_token=challenge["token"])

    def test_lease_expiry_revokes_agent(self, broker):
        broker.update_session("sess-1", interactive=True)
        challenge = broker.issue_grant_challenge()
        broker.grant_agent(1, user_ack=True, challenge_token=challenge["token"])  # 1s lease
        assert broker.check_access() is True
        time.sleep(1.5)
        assert broker.check_access() is False  # Lease expired


class TestHumanPriority:
    def test_user_activity_revokes_agent(self, broker):
        broker.update_session("sess-1", interactive=True)
        challenge = broker.issue_grant_challenge()
        broker.grant_agent(300, user_ack=True, challenge_token=challenge["token"])
        assert broker.check_access() is True
        broker.report_user_activity()
        assert broker.check_access() is False

    def test_stop_now_revokes_agent_and_blocks_access(self, broker):
        broker.update_session("sess-1", interactive=True)
        challenge = broker.issue_grant_challenge()
        broker.grant_agent(300, user_ack=True, challenge_token=challenge["token"])
        assert broker.check_access() is True
        broker.set_user_intent(UserIntent.STOP_NOW)
        assert broker.check_access() is False
        with pytest.raises(PermissionError, match="does not hold control"):
            broker.renew_agent(300)


class TestWinInspectBinding:
    def test_bind_wininspect_syncs_take(self):
        broker = InputBroker()
        mock_client = MagicMock()
        broker.bind_wininspect(mock_client)

        broker.update_session("sess-1", interactive=True)
        challenge = broker.issue_grant_challenge()
        broker.grant_agent(300, user_ack=True, challenge_token=challenge["token"])

        # Should have called control.take on WinInspect
        mock_client.request.assert_called_with("control.take", {
            "controller": "agent", "id": "broker"
        })

    def test_bind_wininspect_syncs_revoke(self):
        broker = InputBroker()
        mock_client = MagicMock()
        broker.bind_wininspect(mock_client)

        broker.update_session("sess-1", interactive=True)
        challenge = broker.issue_grant_challenge()
        broker.grant_agent(300, user_ack=True, challenge_token=challenge["token"])
        mock_client.reset_mock()

        broker.report_user_activity()

        # Should have called control.release on WinInspect
        mock_client.request.assert_called_with("control.release", {
            "controller": "agent", "id": "broker"
        })


class TestTakeControlCallback:
    def test_human_take_control(self, broker):
        broker.update_session("sess-1", interactive=True)
        challenge = broker.issue_grant_challenge()
        broker.grant_agent(300, user_ack=True, challenge_token=challenge["token"])
        assert broker.get_state().control_mode == ControlMode.AGENT

        # Simulate human taking control via WinInspect callback
        broker.take_control("human", "human-1")
        assert broker.get_state().control_mode == ControlMode.USER
        assert broker.check_access() is False

    def test_none_control_release(self, broker):
        broker.update_session("sess-1", interactive=True)
        challenge = broker.issue_grant_challenge()
        broker.grant_agent(300, user_ack=True, challenge_token=challenge["token"])

        broker.take_control("none", "")
        assert broker.get_state().control_mode == ControlMode.USER
