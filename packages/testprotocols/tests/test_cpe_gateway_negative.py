"""Negative-path shape tests for the CPE gateway archetype (verification review, code C1).

A fake with the released shape fails the extended protocols; a fake short of one member
fails each new protocol; a core-only fake is no tier. The positive form of each check is
beside it, so a test that passes proves the member set, not the fake.
"""

from __future__ import annotations

from collections.abc import Iterable

import pytest
from _helpers import protocol_attrs
from testprotocols.admin_credential import AdminCredential
from testprotocols.auto_port_mapping import AutoPortMapping
from testprotocols.device_info import DeviceInfo
from testprotocols.device_lifecycle import DeviceLifecycle
from testprotocols.device_management import DeviceManagement
from testprotocols.devices.cpe_gateway import (
    CpeGatewayDevice,
    CpeGatewayMeshTier,
    CpeGatewayUspTier,
)
from testprotocols.dns_forwarder import DnsForwarder
from testprotocols.host_filter import HostFilter
from testprotocols.host_table import HostTable
from testprotocols.l2_bridge import L2Bridge
from testprotocols.ntp_config import NtpConfig
from testprotocols.tr069_client import Tr069Client
from testprotocols.usp_agent import UspAgent
from testprotocols.wan_connection import WanConnection
from testprotocols.wifi_onboarding import WifiOnboarding

#: The members this PR adds to a released protocol (changelog, *Breaking for driver authors*).
ADDED: dict[type, frozenset[str]] = {
    DeviceInfo: frozenset(
        {"manufacturer", "serial_number", "software_version", "oui", "hardware_version"}
    ),
    DeviceLifecycle: frozenset(
        {"upgrade_firmware", "export_configuration", "import_configuration", "verify_booting"}
    ),
    Tr069Client: frozenset({"set_acs", "get_acs"}),
    NtpConfig: frozenset({"get_sync_state"}),
    WifiOnboarding: frozenset({"cancel_wps", "get_wps_state"}),
    DeviceManagement: frozenset({"read_cpu_load"}),
}

NEW_PROTOCOLS: tuple[type, ...] = (
    WanConnection,
    DnsForwarder,
    L2Bridge,
    HostTable,
    HostFilter,
    AutoPortMapping,
    AdminCredential,
    UspAgent,
)


def fake_with(members: Iterable[str]) -> object:
    """An instance whose attributes are exactly *members* (each a no-op callable)."""

    def member(self: object, *args: object, **kwargs: object) -> None:
        return None

    return type("Fake", (), dict.fromkeys(members, member))()


@pytest.mark.parametrize("protocol", list(ADDED), ids=lambda p: p.__name__)
def test_the_released_shape_fails_an_extended_protocol(protocol: type) -> None:
    members = protocol_attrs(protocol)
    assert ADDED[protocol] <= members
    assert not isinstance(fake_with(members - ADDED[protocol]), protocol)
    assert isinstance(fake_with(members), protocol)


@pytest.mark.parametrize("protocol", NEW_PROTOCOLS, ids=lambda p: p.__name__)
def test_a_fake_short_of_one_member_fails_a_new_protocol(protocol: type) -> None:
    members = protocol_attrs(protocol)
    assert isinstance(fake_with(members), protocol)
    for missing in sorted(members):
        assert not isinstance(fake_with(members - {missing}), protocol), missing


@pytest.mark.parametrize("tier", [CpeGatewayMeshTier, CpeGatewayUspTier], ids=lambda t: t.__name__)
def test_a_core_only_fake_is_not_a_tier(tier: type) -> None:
    core = fake_with(protocol_attrs(CpeGatewayDevice))
    assert isinstance(core, CpeGatewayDevice)
    assert not isinstance(core, tier)
    assert isinstance(fake_with(protocol_attrs(tier)), tier)
