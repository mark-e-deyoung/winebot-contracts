"""
Runtime lifecycle plugin interface.

Each runtime type (Win VM, Wine Docker, Physical PC, Windows Sandbox)
implements this interface so the fleet CLI can manage all types through
a single API.

Usage:
    from winebot_contracts.plugins import RuntimePlugin, RuntimeStatus

    class VmPlugin(RuntimePlugin):
        async def provision(self, config):
            ...build VM image...
            return "vm-abc123"

        async def start(self, instance_id):
            ...boot VM via libvirt...
            return {"host": "10.0.0.1", "port": 1985}
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ── Status types ─────────────────────────────────────────────────────────

class RuntimeState:
    PROVISIONING = "PROVISIONING"
    RUNNING = "RUNNING"
    SUSPENDED = "SUSPENDED"
    DEPROVISIONING = "DEPROVISIONING"
    DESTROYED = "DESTROYED"


@dataclass
class RuntimeStatus:
    """Snapshot of a runtime instance's current state."""

    instance_id: str
    state: str  # one of RuntimeState values
    runtime_type: str  # "win-vm" | "wine-docker" | "physical" | "sandbox"
    host: str = ""
    port: int = 1985
    daemon_ready: bool = False
    controller: str = ""  # "none" | "human" | "agent"
    lease_remaining: float = 0.0
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "instance_id": self.instance_id,
            "state": self.state,
            "runtime_type": self.runtime_type,
            "host": self.host,
            "port": self.port,
            "daemon_ready": self.daemon_ready,
            "controller": self.controller,
            "lease_remaining": self.lease_remaining,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class ConnectionInfo:
    """How to reach a running instance."""

    host: str
    port: int = 1985
    transport: str = "tcp"  # "tcp" | "pipe" | "http"
    auth_token: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Plugin interface ─────────────────────────────────────────────────────

class RuntimePlugin(ABC):
    """Interface for runtime lifecycle management.

    Each runtime type implements these methods. The fleet CLI calls
    them through a registry that maps runtime_type → plugin class.
    """

    @property
    @abstractmethod
    def runtime_type(self) -> str:
        """Unique identifier: 'win-vm', 'wine-docker', 'physical', 'sandbox'."""
        ...

    @abstractmethod
    async def provision(self, config: dict[str, Any]) -> str:
        """Create the runtime image/environment.

        Args:
            config: Runtime-specific configuration (image name, Dockerfile,
                   Packer template, etc.)

        Returns:
            instance_id: Unique identifier for the provisioned instance.
        """
        ...

    @abstractmethod
    async def start(self, instance_id: str) -> ConnectionInfo:
        """Boot the runtime and return connection info.

        The runtime should have WinInspect running and accepting
        TCP connections by the time this returns.

        Args:
            instance_id: From provision().

        Returns:
            ConnectionInfo with host/port for WinInspect daemon.
        """
        ...

    @abstractmethod
    async def stop(self, instance_id: str) -> None:
        """Gracefully shut down the runtime.

        Should export logs/artifacts before stopping if export=True
        was passed to deprovision().
        """
        ...

    @abstractmethod
    async def deprovision(self, instance_id: str, export: bool = True) -> Optional[Path]:
        """Destroy the runtime and optionally export artifacts.

        Args:
            instance_id: Instance to destroy.
            export: If True, export audit logs, recordings, and
                   diagnostic bundles before destroying.

        Returns:
            Path to exported artifacts archive, or None if no export.
        """
        ...

    @abstractmethod
    async def status(self, instance_id: str) -> RuntimeStatus:
        """Query the current state of a runtime instance."""
        ...

    async def execute_rpc(self, instance_id: str, method: str,
                          params: Optional[dict] = None) -> dict:
        """Optional: Execute a WinInspect RPC on the instance.

        Default implementation connects via TCP. Override for
        runtime-specific transport (e.g., SSH tunneling, TLS).
        """
        import socket, struct, json, uuid

        info = await self.start(instance_id)
        rid = f"fleet-{uuid.uuid4().hex[:8]}"
        payload = {"id": rid, "method": method, "params": params or {}}
        data = json.dumps(payload, separators=(",", ":")).encode()

        with socket.create_connection((info.host, info.port), timeout=10) as sock:
            sock.settimeout(10)
            # Read hello
            header = sock.recv(4)
            length = struct.unpack("!I", header)[0] & 0x7FFFFFFF
            sock.recv(length)
            # Send request
            sock.sendall(struct.pack("!I", len(data)) + data)
            # Read response
            header = sock.recv(4)
            length = struct.unpack("!I", header)[0] & 0x7FFFFFFF
            resp = json.loads(sock.recv(length).decode())
        return resp


# ── Registry ─────────────────────────────────────────────────────────────

_registry: dict[str, type[RuntimePlugin]] = {}


def register(plugin_class: type[RuntimePlugin]) -> type[RuntimePlugin]:
    """Decorator to register a runtime plugin."""
    rt = plugin_class.runtime_type
    if not isinstance(rt, str) or not rt:
        raise ValueError(f"runtime_type must be a non-empty string, got {rt!r}")
    _registry[rt] = plugin_class
    return plugin_class


def get_plugin(runtime_type: str) -> RuntimePlugin:
    """Get an instance of the plugin for the given runtime type."""
    cls = _registry.get(runtime_type)
    if cls is None:
        available = ", ".join(sorted(_registry))
        raise KeyError(f"No plugin registered for '{runtime_type}'. Available: [{available}]")
    return cls()


def list_types() -> list[str]:
    """List all registered runtime types."""
    return sorted(_registry)
