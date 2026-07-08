"""
InputBroker — shared control plane for human/agent handoff.

Provides a consistent control policy across WinBot and WineBot runtimes.
Human always takes precedence and can seize control from agents at any time.

Two-layer architecture:
  1. InputBroker (Python) — challenge tokens, session policy, user intent
  2. WinInspect ControlManager (C++) — lease enforcement, audit log

Usage:
    from winebot_contracts.broker import InputBroker, broker as global_broker

    # Agent requests control
    if await broker.check_access():
        await broker.take_control("agent", "my-agent-id")

    # Human is interacting — broker detects and releases agent
    await broker.report_user_activity()  # triggers agent revoke if active

    # Check state
    state = broker.get_state()
    print(state.control_mode, state.lease_expiry)
"""

import secrets
import threading
import time
from enum import Enum
from typing import Optional


class ControlMode(str, Enum):
    USER = "USER"
    AGENT = "AGENT"


class ControlPolicyMode(str, Enum):
    HUMAN_ONLY = "human-only"
    AGENT_ONLY = "agent-only"
    HYBRID = "hybrid"


class UserIntent(str, Enum):
    WAIT = "WAIT"
    SAFE_INTERRUPT = "SAFE_INTERRUPT"
    STOP_NOW = "STOP_NOW"


class AgentStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class ControlState:
    """Immutable snapshot of broker state."""

    def __init__(
        self,
        session_id: str = "unknown",
        interactive: bool = False,
        control_mode: ControlMode = ControlMode.USER,
        user_intent: UserIntent = UserIntent.WAIT,
        agent_status: AgentStatus = AgentStatus.IDLE,
        instance_control_mode: ControlPolicyMode = ControlPolicyMode.HYBRID,
        session_control_mode: ControlPolicyMode = ControlPolicyMode.HYBRID,
        effective_control_mode: ControlPolicyMode = ControlPolicyMode.HYBRID,
        lease_expiry: Optional[float] = None,
    ):
        self.session_id = session_id
        self.interactive = interactive
        self.control_mode = control_mode
        self.user_intent = user_intent
        self.agent_status = agent_status
        self.instance_control_mode = instance_control_mode
        self.session_control_mode = session_control_mode
        self.effective_control_mode = effective_control_mode
        self.lease_expiry = lease_expiry

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "interactive": self.interactive,
            "control_mode": self.control_mode.value,
            "user_intent": self.user_intent.value,
            "agent_status": self.agent_status.value,
            "instance_control_mode": self.instance_control_mode.value,
            "session_control_mode": self.session_control_mode.value,
            "effective_control_mode": self.effective_control_mode.value,
            "lease_expiry": self.lease_expiry,
        }


class InputBroker:
    """Shared control plane policy engine.

    Manages human/agent handoff with:
    - Human always wins (takes precedence over any agent)
    - Challenge tokens for agent control grant
    - Lease-based agent control with auto-release
    - User intent communication (WAIT / STOP_NOW)
    - Instance-level and session-level policy inheritance
    """

    def __init__(self):
        self._lock = threading.RLock()
        self.state = ControlState()
        self.last_user_activity = 0.0
        self.last_agent_activity = 0.0
        self._grant_challenge_token: Optional[str] = None
        self._grant_challenge_expiry: float = 0.0
        self._wininspect_client = None  # Optional: connect to WinInspect ControlManager

    def bind_wininspect(self, client):
        """Bind to a WinInspect RPC client for daemon-level enforcement.

        Args:
            client: An object with request(method, params) → dict.
        """
        self._wininspect_client = client

    @property
    def last_activity(self) -> float:
        return max(self.last_user_activity, self.last_agent_activity)

    def _compute_effective_mode(self) -> ControlPolicyMode:
        if (
            self.state.instance_control_mode == ControlPolicyMode.HUMAN_ONLY
            or self.state.session_control_mode == ControlPolicyMode.HUMAN_ONLY
        ):
            return ControlPolicyMode.HUMAN_ONLY
        if (
            self.state.instance_control_mode == ControlPolicyMode.AGENT_ONLY
            or self.state.session_control_mode == ControlPolicyMode.AGENT_ONLY
        ):
            return ControlPolicyMode.AGENT_ONLY
        return ControlPolicyMode.HYBRID

    def set_instance_control_mode(self, mode: ControlPolicyMode) -> None:
        with self._lock:
            self.state.instance_control_mode = mode
            self.state.effective_control_mode = self._compute_effective_mode()
            if self.state.effective_control_mode == ControlPolicyMode.AGENT_ONLY:
                self.state.control_mode = ControlMode.AGENT
            else:
                self.state.control_mode = ControlMode.USER
                self.state.lease_expiry = None

    def issue_grant_challenge(self, ttl_seconds: int = 30) -> dict:
        """Issue a one-time challenge token for control grant authorization."""
        with self._lock:
            token = secrets.token_urlsafe(18)
            now = time.time()
            self._grant_challenge_token = token
            self._grant_challenge_expiry = now + max(5, ttl_seconds)
            return {"token": token, "expires_epoch": self._grant_challenge_expiry}

    def set_session_control_mode(self, mode: ControlPolicyMode) -> None:
        with self._lock:
            self.state.session_control_mode = mode
            self.state.effective_control_mode = self._compute_effective_mode()
            if self.state.effective_control_mode == ControlPolicyMode.AGENT_ONLY:
                self.state.control_mode = ControlMode.AGENT
            else:
                self.state.control_mode = ControlMode.USER
                self.state.lease_expiry = None

    def update_session(
        self,
        session_id: str,
        interactive: bool,
        session_control_mode: ControlPolicyMode = ControlPolicyMode.HYBRID,
    ) -> None:
        with self._lock:
            self.state.session_id = session_id
            self.state.interactive = interactive
            self.state.effective_control_mode = self._compute_effective_mode()

            if self.state.effective_control_mode == ControlPolicyMode.AGENT_ONLY:
                self.state.control_mode = ControlMode.AGENT
                self.state.lease_expiry = None
                return
            if self.state.effective_control_mode == ControlPolicyMode.HUMAN_ONLY:
                self.state.control_mode = ControlMode.USER
                self.state.lease_expiry = None
                return

            if not interactive:
                self.state.control_mode = ControlMode.AGENT
            else:
                if self.state.control_mode == ControlMode.AGENT:
                    self._revoke_agent("session_became_interactive")
                self.state.control_mode = ControlMode.USER

    def grant_agent(
        self,
        lease_seconds: int,
        user_ack: bool = False,
        challenge_token: str = "",
    ) -> None:
        """Grant control to agent. Requires user acknowledgement + challenge."""
        with self._lock:
            if not user_ack:
                raise PermissionError("User acknowledgement required to grant agent control")

            now = time.time()
            if (
                not self._grant_challenge_token
                or now > self._grant_challenge_expiry
                or challenge_token != self._grant_challenge_token
            ):
                raise PermissionError("Valid one-time challenge token required")

            self._grant_challenge_token = None
            self._grant_challenge_expiry = 0.0

            if self.state.effective_control_mode == ControlPolicyMode.HUMAN_ONLY:
                raise PermissionError("Control mode is human-only")

            if not self.state.interactive:
                return  # Always implicit in non-interactive

            self.state.control_mode = ControlMode.AGENT
            self.state.lease_expiry = time.time() + lease_seconds
            self.state.user_intent = UserIntent.WAIT

            # Sync to WinInspect if bound
            if self._wininspect_client:
                self._wininspect_client.request("control.take", {
                    "controller": "agent", "id": "broker"
                })

    def renew_agent(self, lease_seconds: int) -> None:
        with self._lock:
            if self.state.control_mode != ControlMode.AGENT:
                raise PermissionError("Agent does not hold control")
            if self.state.user_intent == UserIntent.STOP_NOW:
                raise PermissionError("User requested STOP_NOW")
            self.state.lease_expiry = time.time() + lease_seconds

    def _revoke_agent(self, reason: str) -> None:
        self.state.control_mode = ControlMode.USER
        self.state.lease_expiry = None
        self.state.agent_status = AgentStatus.STOPPING

        # Sync to WinInspect if bound
        if self._wininspect_client:
            self._wininspect_client.request("control.release", {
                "controller": "agent", "id": "broker"
            })

    def report_user_activity(self) -> None:
        with self._lock:
            self.last_user_activity = time.time()
            if self.state.control_mode == ControlMode.AGENT:
                self._revoke_agent("user_input_override")

    def report_agent_activity(self) -> None:
        with self._lock:
            self.last_agent_activity = time.time()

    def set_user_intent(self, intent: UserIntent) -> None:
        with self._lock:
            self.state.user_intent = intent
            if intent == UserIntent.STOP_NOW:
                self._revoke_agent("user_stop_now")

    def check_access(self) -> bool:
        """Returns True if agent is allowed to execute operations."""
        with self._lock:
            if self.state.effective_control_mode == ControlPolicyMode.HUMAN_ONLY:
                return False
            if self.state.effective_control_mode == ControlPolicyMode.AGENT_ONLY:
                return self.state.control_mode == ControlMode.AGENT
            if not self.state.interactive:
                return True
            if self.state.control_mode != ControlMode.AGENT:
                return False
            if self.state.lease_expiry and time.time() > self.state.lease_expiry:
                self._revoke_agent("lease_expired")
                return False
            if self.state.user_intent == UserIntent.STOP_NOW:
                self._revoke_agent("user_stop_now")
                return False
            return True

    def take_control(self, controller: str, controller_id: str) -> bool:
        """Called by WinInspect ControlManager callback when control changes."""
        with self._lock:
            if controller == "human":
                if self.state.control_mode == ControlMode.AGENT:
                    self._revoke_agent("human_took_control")
                self.state.control_mode = ControlMode.USER
                return True
            elif controller == "agent":
                if self.state.effective_control_mode == ControlPolicyMode.HUMAN_ONLY:
                    return False
                self.state.control_mode = ControlMode.AGENT
                return True
            elif controller == "none":
                self.state.control_mode = ControlMode.USER
                self.state.lease_expiry = None
                return True
            return False

    def get_state(self) -> ControlState:
        with self._lock:
            return self.state


# Global singleton for shared use
broker = InputBroker()
