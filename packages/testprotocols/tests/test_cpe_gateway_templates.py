"""Protocol shapes of the CPE gateway capabilities (design §4, §6)."""

from __future__ import annotations

import dataclasses
import importlib
import inspect

import pytest
from _helpers import protocol_attrs

PROTOCOLS = [
    (
        "WanConnection",
        "testprotocols.wan_connection",
        {
            "set_wan_connection",
            "get_wan_connection",
            "list_wan_connections",
            "get_wan_state",
            "reset_session",
        },
    ),
    (
        "DnsForwarder",
        "testprotocols.dns_forwarder",
        {
            "set_upstreams",
            "get_upstreams",
            "add_host_override",
            "remove_host_override",
            "list_host_overrides",
            "set_rebind_protection",
            "get_rebind_protection",
        },
    ),
    (
        "L2Bridge",
        "testprotocols.l2_bridge",
        {
            "create_bridge",
            "delete_bridge",
            "list_bridges",
            "get_bridge",
            "add_member",
            "remove_member",
            "get_members",
        },
    ),
    ("HostTable", "testprotocols.host_table", {"list_hosts", "get_host"}),
    (
        "HostFilter",
        "testprotocols.host_filter",
        {"block_host", "unblock_host", "get_host_block", "list_host_blocks"},
    ),
    (
        "AutoPortMapping",
        "testprotocols.auto_port_mapping",
        {"set_enabled", "get_enabled", "list_mappings"},
    ),
    ("AdminCredential", "testprotocols.admin_credential", {"set_password", "list_accounts"}),
]

MULTI_STEP_WRITES = {
    "set_wan_connection": ("testprotocols.wan_connection", "WanConnection"),
    "set_upstreams": ("testprotocols.dns_forwarder", "DnsForwarder"),
    "create_bridge": ("testprotocols.l2_bridge", "L2Bridge"),
    "block_host": ("testprotocols.host_filter", "HostFilter"),
}


@pytest.mark.parametrize(("name", "module", "members"), PROTOCOLS, ids=[p[0] for p in PROTOCOLS])
def test_protocol_members(name: str, module: str, members: set[str]) -> None:
    proto = getattr(importlib.import_module(module), name)
    assert protocol_attrs(proto) == members
    assert getattr(proto, "_is_runtime_protocol", False)


@pytest.mark.parametrize(("name", "module", "members"), PROTOCOLS, ids=[p[0] for p in PROTOCOLS])
def test_every_member_has_a_docstring_without_vendor_words(
    name: str, module: str, members: set[str]
) -> None:
    proto = getattr(importlib.import_module(module), name)
    for member in members:
        doc = inspect.getdoc(getattr(proto, member)) or ""
        assert doc, f"{name}.{member} has no docstring"
        assert "NotImplementedError" not in doc


@pytest.mark.parametrize("member", sorted(MULTI_STEP_WRITES))
def test_multi_step_writes_state_their_failure_outcome(member: str) -> None:
    module, name = MULTI_STEP_WRITES[member]
    owner = getattr(importlib.import_module(module), name)
    assert "rejected at any step raises naming the step" in (
        inspect.getdoc(getattr(owner, member)) or ""
    )


def test_reexported() -> None:
    import testprotocols

    for name, _, _ in PROTOCOLS:
        assert name in testprotocols.__all__
        assert hasattr(testprotocols, name)


# `dataclasses` is used by the extension tests appended in later tasks.
_ = dataclasses


def test_device_health_split() -> None:
    from _helpers import protocol_mro
    from testprotocols.device_health import DeviceHealth
    from testprotocols.device_management import DeviceManagement

    assert protocol_attrs(DeviceHealth) == {
        "is_online",
        "get_seconds_uptime",
        "read_cpu_load",
        "read_memory_utilization",
        "read_running_processes",
        "read_log_entries",
    }
    assert DeviceHealth in protocol_mro(DeviceManagement)
    assert "read_cpu_load" in protocol_attrs(DeviceManagement)
    assert "get_load_avg" in protocol_attrs(DeviceManagement)
    assert protocol_attrs(DeviceHealth) < protocol_attrs(DeviceManagement)


def test_cpu_load_record() -> None:
    from testprotocols.models.device_management import CpuLoad

    assert [f.name for f in dataclasses.fields(CpuLoad)] == ["percent", "load_average_1m"]
    assert CpuLoad.__dataclass_params__.frozen  # type: ignore[attr-defined]
