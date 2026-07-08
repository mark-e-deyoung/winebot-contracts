"""Tests for the runtime lifecycle plugin interface."""

import pytest
from winebot_contracts.plugins import (
    ConnectionInfo,
    RuntimePlugin,
    RuntimeState,
    RuntimeStatus,
    get_plugin,
    list_types,
    register,
)


class TestRuntimeState:
    def test_constants_are_distinct(self):
        states = {RuntimeState.PROVISIONING, RuntimeState.RUNNING,
                  RuntimeState.SUSPENDED, RuntimeState.DEPROVISIONING,
                  RuntimeState.DESTROYED}
        assert len(states) == 5


class TestRuntimeStatus:
    def test_default_values(self):
        s = RuntimeStatus(instance_id="test-1", state=RuntimeState.RUNNING,
                          runtime_type="wine-docker")
        assert s.host == ""
        assert s.port == 1985
        assert s.daemon_ready is False
        assert s.error is None

    def test_to_dict(self):
        s = RuntimeStatus(instance_id="test-1", state=RuntimeState.RUNNING,
                          runtime_type="win-vm", host="10.0.0.1")
        d = s.to_dict()
        assert d["instance_id"] == "test-1"
        assert d["host"] == "10.0.0.1"
        assert d["runtime_type"] == "win-vm"


class TestRegistry:
    def test_register_and_get(self):
        @register
        class TestPlugin(RuntimePlugin):
            runtime_type = "test-dummy"

            async def provision(self, config): return "test-1"
            async def start(self, instance_id): return ConnectionInfo(host="localhost")
            async def stop(self, instance_id): pass
            async def deprovision(self, instance_id, export=True): return None
            async def status(self, instance_id):
                return RuntimeStatus(instance_id="test-1", state=RuntimeState.RUNNING,
                                     runtime_type="test-dummy")

        plugin = get_plugin("test-dummy")
        assert isinstance(plugin, TestPlugin)

    def test_list_types_includes_registered(self):
        assert "test-dummy" in list_types()

    def test_get_unknown_raises(self):
        with pytest.raises(KeyError, match="No plugin registered"):
            get_plugin("nonexistent")

    def test_register_empty_type_raises(self):
        with pytest.raises(ValueError):
            class BadPlugin(RuntimePlugin):
                runtime_type = ""
                async def provision(self, config): return ""
                async def start(self, instance_id): return ConnectionInfo(host="")
                async def stop(self, instance_id): pass
                async def deprovision(self, instance_id, export=True): return None
                async def status(self, instance_id):
                    return RuntimeStatus("", RuntimeState.RUNNING, "")

            register(BadPlugin)
