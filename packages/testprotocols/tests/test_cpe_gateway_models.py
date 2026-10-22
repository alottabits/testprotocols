"""Shape tests for the CPE gateway records and vocabularies (design §6, M6 to M12, M35)."""

from __future__ import annotations

import dataclasses
import datetime
from enum import StrEnum

import pytest
from _helpers import assert_str_value
from testprotocols.models import cpe_gateway as m


def _fields(cls: type) -> dict[str, tuple[str, object]]:
    return {f.name: (str(f.type), f.default) for f in dataclasses.fields(cls)}


@pytest.mark.parametrize(
    ("enum", "names"),
    [
        (m.WanMode, ("DHCP", "STATIC", "PPPOE")),
        (m.WanIpv6Mode, ("DISABLED", "DHCPV6_PD", "SLAAC", "STATIC")),
        (
            m.WanStatus,
            (
                "UNCONFIGURED",
                "CONNECTING",
                "AUTHENTICATING",
                "CONNECTED",
                "DISCONNECTING",
                "DISCONNECTED",
            ),
        ),
        (m.ProvisioningMode, ("IPV4", "IPV6", "DUAL_STACK")),
        (m.BridgeMemberKind, ("PORT", "WIRELESS_NETWORK")),
        (m.HostAttachment, ("ETHERNET", "WIFI")),
        (m.AutoMappingProtocol, ("UPNP_IGD", "PCP", "NAT_PMP")),
        (m.UspTransport, ("WEBSOCKET", "MQTT", "STOMP")),
    ],
)
def test_closed_sets(enum: type[StrEnum], names: tuple[str, ...]) -> None:
    assert tuple(member.name for member in enum) == names
    for member in enum:
        assert_str_value(member, member.name.lower())


def test_weekday_is_iso_numbered() -> None:
    assert [d.value for d in m.Weekday] == [1, 2, 3, 4, 5, 6, 7]
    assert m.Weekday.MONDAY.value == 1
    assert m.Weekday.SUNDAY.value == 7


@pytest.mark.parametrize(
    "cls",
    [
        m.PppoeCredentials,
        m.StaticAddressing,
        m.WanVlan,
        m.WanIpv6,
        m.WanConnectionConfig,
        m.WanConnectionState,
        m.DnsUpstream,
        m.DnsHostOverride,
        m.BridgeMember,
        m.BridgeConfig,
        m.BridgeMemberState,
        m.LanHost,
        m.WeeklySchedule,
        m.HostBlock,
        m.AutoPortMappingEntry,
        m.UspController,
        m.UspAgentState,
    ],
)
def test_records_are_frozen(cls: type) -> None:
    assert dataclasses.is_dataclass(cls)
    assert cls.__dataclass_params__.frozen  # type: ignore[attr-defined]  # CPython dataclass bookkeeping, not in typeshed


def test_record_fields() -> None:
    assert list(_fields(m.BridgeConfig)) == ["name", "stp_mode"]
    assert _fields(m.BridgeConfig)["stp_mode"][1] is None
    assert _fields(m.PppoeCredentials)["password"][1] is dataclasses.MISSING
    assert _fields(m.StaticAddressing)["dns_servers"][1] == ()
    assert _fields(m.DnsUpstream)["port"][1] == 53
    assert _fields(m.HostBlock)["enabled"][1] is True
    assert all(f.default is dataclasses.MISSING for f in dataclasses.fields(m.WanConnectionState))
    assert list(_fields(m.WanConnectionConfig)) == [
        "name",
        "mode",
        "pppoe",
        "static",
        "vlan",
        "ipv6",
    ]
    assert list(_fields(m.LanHost)) == [
        "mac",
        "ipv4_address",
        "ipv6_addresses",
        "hostname",
        "attachment",
        "interface",
        "active",
    ]
    assert list(_fields(m.UspController)) == [
        "endpoint_id",
        "transport",
        "host",
        "port",
        "path",
        "tls",
    ]


def test_schedule_holds_times() -> None:
    s = m.WeeklySchedule(frozenset({m.Weekday.MONDAY}), datetime.time(22, 0), datetime.time(6, 0))
    assert s.end < s.start  # past midnight is allowed (design §6)


def test_reexported_from_models_package() -> None:
    import testprotocols.models as models

    for name in (
        "WanMode",
        "WanConnectionConfig",
        "WanConnectionState",
        "DnsUpstream",
        "BridgeConfig",
        "LanHost",
        "HostBlock",
        "WeeklySchedule",
        "Weekday",
        "AutoPortMappingEntry",
        "UspController",
    ):
        assert name in models.__all__
        assert hasattr(models, name)


def test_usp_agent_state_carries_the_endpoint_only() -> None:
    """No reviewed family publishes a connection state, so ``connected`` is dropped (§6)."""
    assert list(_fields(m.UspAgentState)) == ["endpoint_id"]
