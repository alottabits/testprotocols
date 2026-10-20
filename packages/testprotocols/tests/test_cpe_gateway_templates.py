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
    (
        "UspAgent",
        "testprotocols.usp_agent",
        {"set_controller", "get_controller", "get_agent_state"},
    ),
]

MULTI_STEP_WRITES = {
    "set_wan_connection": ("testprotocols.wan_connection", "WanConnection"),
    "set_upstreams": ("testprotocols.dns_forwarder", "DnsForwarder"),
    "create_bridge": ("testprotocols.l2_bridge", "L2Bridge"),
    "block_host": ("testprotocols.host_filter", "HostFilter"),
    "set_controller": ("testprotocols.usp_agent", "UspAgent"),
    # the removals the §6 "Method grain" table pairs with the multi-step writes above
    "unblock_host": ("testprotocols.host_filter", "HostFilter"),
    "delete_bridge": ("testprotocols.l2_bridge", "L2Bridge"),
}

BY_NAME_MEMBERS = [
    ("testprotocols.wan_connection", "WanConnection", "get_wan_connection"),
    ("testprotocols.wan_connection", "WanConnection", "get_wan_state"),
    ("testprotocols.wan_connection", "WanConnection", "reset_session"),
    ("testprotocols.dns_forwarder", "DnsForwarder", "remove_host_override"),
    ("testprotocols.l2_bridge", "L2Bridge", "delete_bridge"),
    ("testprotocols.l2_bridge", "L2Bridge", "get_bridge"),
    ("testprotocols.l2_bridge", "L2Bridge", "add_member"),
    ("testprotocols.l2_bridge", "L2Bridge", "remove_member"),
    ("testprotocols.l2_bridge", "L2Bridge", "get_members"),
    ("testprotocols.host_table", "HostTable", "get_host"),
    ("testprotocols.host_filter", "HostFilter", "unblock_host"),
    ("testprotocols.host_filter", "HostFilter", "get_host_block"),
    ("testprotocols.admin_credential", "AdminCredential", "set_password"),
]


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


def test_device_info_identity_properties() -> None:
    from testprotocols.device_info import DeviceInfo

    assert protocol_attrs(DeviceInfo) == {
        "model",
        "manufacturer",
        "serial_number",
        "software_version",
        "oui",
        "hardware_version",
    }
    for name in ("manufacturer", "serial_number", "software_version", "oui", "hardware_version"):
        assert isinstance(inspect.getattr_static(DeviceInfo, name), property)


def test_lifecycle_extension_and_rename() -> None:
    from testprotocols.device_lifecycle import DeviceLifecycle

    assert {
        "upgrade_firmware",
        "export_configuration",
        "import_configuration",
        "verify_booting",
        "verify_cpe_is_booting",
    } <= protocol_attrs(DeviceLifecycle)
    doc = inspect.getdoc(getattr(DeviceLifecycle, "verify_cpe_is_booting")) or ""
    assert "Deprecated: use verify_booting." in doc


def test_tr069_client_acs_members_and_neutral_inform() -> None:
    from testprotocols.tr069_client import Tr069Client

    assert {"set_acs", "get_acs"} <= protocol_attrs(Tr069Client)
    doc = inspect.getdoc(Tr069Client.force_inform) or ""
    assert "ubus" not in doc
    assert "NotSupportedError" in doc


def test_acs_config_and_image_source_records() -> None:
    from testprotocols.models.device_management import ImageSource
    from testprotocols.models.tr069 import AcsConfig

    assert [f.name for f in dataclasses.fields(AcsConfig)] == [
        "enabled",
        "url",
        "username",
        "password",
        "periodic_inform_enabled",
        "periodic_inform_interval_s",
        "connection_request_username",
        "connection_request_password",
    ]
    assert dataclasses.fields(ImageSource)[1].default is None
    assert ImageSource.__dataclass_params__.frozen  # type: ignore[attr-defined]


def test_ntp_sync_state_extension() -> None:
    from testprotocols.models.switch import NtpSyncState, NtpSyncStatus
    from testprotocols.ntp_config import NtpConfig

    assert protocol_attrs(NtpConfig) == {"set_ntp_servers", "get_ntp_servers", "get_sync_state"}
    assert [m.name for m in NtpSyncStatus] == ["SYNCHRONISED", "UNSYNCHRONISED", "DISABLED"]
    assert [f.name for f in dataclasses.fields(NtpSyncState)] == [
        "status",
        "server",
        "offset_ms",
        "last_sync",
    ]


def test_wps_cancel_and_state() -> None:
    from testprotocols.models.wifi import WpsMethod, WpsSessionState, WpsState
    from testprotocols.wifi_onboarding import WifiOnboarding

    assert {"cancel_wps", "get_wps_state"} <= protocol_attrs(WifiOnboarding)
    assert [m.name for m in WpsSessionState] == ["IDLE", "ACTIVE", "SUCCESS", "FAILED", "TIMEOUT"]
    assert [m.name for m in WpsMethod] == ["PUSH_BUTTON", "PIN"]
    assert [f.name for f in dataclasses.fields(WpsState)] == ["session", "method", "remaining_s"]
    module_doc = inspect.getdoc(importlib.import_module("testprotocols.wifi_onboarding")) or ""
    assert "NotImplementedError" not in module_doc


def test_defaulted_fields() -> None:
    from testprotocols.models.switch_routing import InterfaceDhcpConfig
    from testprotocols.models.wifi import MeshRole, WifiMeshNode

    cfg = InterfaceDhcpConfig("br-lan")
    assert cfg.pool_start is None
    assert cfg.pool_end is None
    node = WifiMeshNode("aa:bb:cc:dd:ee:ff", MeshRole.AGENT, None, 1)
    assert node.backhaul_link is None


def test_generalised_docstrings() -> None:
    for module in ("testprotocols.wan_link_admin", "testprotocols.wifi_mesh"):
        doc = inspect.getdoc(importlib.import_module(module)) or ""
        assert "NotImplementedError" not in doc
    # M28: the lever is published by closed gateways too, not only by the Linux twin
    assert "closed gateway" in (
        inspect.getdoc(importlib.import_module("testprotocols.wan_link_admin")) or ""
    )


@pytest.mark.parametrize(
    ("module", "name", "member"), BY_NAME_MEMBERS, ids=[m[2] for m in BY_NAME_MEMBERS]
)
def test_by_name_members_state_the_unknown_name_outcome(
    module: str, name: str, member: str
) -> None:
    """A member keyed by a name says what an unknown name does (the house form: ``KeyError``)."""
    owner = getattr(importlib.import_module(module), name)
    assert "Raises ``KeyError``" in (inspect.getdoc(getattr(owner, member)) or "")
