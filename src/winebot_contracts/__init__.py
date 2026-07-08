"""winebot-contracts — shared control plane, runtime plugins, and conformance tests."""

from .broker import (
    AgentStatus,
    ControlMode,
    ControlPolicyMode,
    ControlState,
    InputBroker,
    UserIntent,
    broker,
)
from .plugins import (
    ConnectionInfo,
    RuntimePlugin,
    RuntimeState,
    RuntimeStatus,
    get_plugin,
    list_types,
    register,
)

__all__ = [
    "AgentStatus",
    "ConnectionInfo",
    "ControlMode",
    "ControlPolicyMode",
    "ControlState",
    "InputBroker",
    "RuntimePlugin",
    "RuntimeState",
    "RuntimeStatus",
    "UserIntent",
    "broker",
    "get_plugin",
    "list_types",
    "register",
]
