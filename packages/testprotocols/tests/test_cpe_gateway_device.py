"""The CPE gateway archetype, its tiers and the superseded class (design §3, §4; M1 to M5, M36)."""

from __future__ import annotations

import sys

import pytest
from _helpers import protocol_attrs, protocol_mro
from testprotocols.devices import all_device_types, get_device_type
from testprotocols.devices.cpe_gateway import (
    CpeGatewayDevice,
    CpeGatewayMeshTier,
    CpeGatewayUspTier,
)

CORE = frozenset(
    {
        "wan_connection",
        "wan_admin",
        "dhcp_client",
        "port_status",
        "interface_dhcp",
        "dns_forwarder",
        "l2_bridge",
        "wifi_radio",
        "wifi_bss",
        "wifi_stations",
        "wifi_onboarding",
        "wifi_transitions",
        "firewall_zones",
        "firewall",
        "host_filter",
        "auto_port_mapping",
        "hosts",
        "info",
        "health",
        "syslog",
        "ntp",
        "device_lifecycle",
        "admin_credential",
        "tr069_client",
        "wan_endpoint",
        "lan_endpoint",
        "device_name",
        "device_type",
    }
)


def test_core_members_and_registration() -> None:
    assert protocol_attrs(CpeGatewayDevice) == CORE
    spec = get_device_type("cpe_gateway")
    assert spec is not None
    assert spec.protocol is CpeGatewayDevice


@pytest.mark.parametrize(
    ("tier", "member"),
    [
        (CpeGatewayMeshTier, "wifi_mesh"),
        (CpeGatewayUspTier, "usp_agent"),
    ],
)
def test_tiers_are_unregistered_supersets(tier: type, member: str) -> None:
    assert CpeGatewayDevice in protocol_mro(tier)
    assert protocol_attrs(tier) == CORE | {member}
    assert all(spec.protocol is not tier for spec in all_device_types().values())


def test_superseded_class_is_marked_and_still_registered() -> None:
    spec = get_device_type("linux_cpe")
    assert spec is not None
    cpe = spec.protocol
    assert cpe.__name__ == "CpeDevice"
    if sys.version_info >= (3, 13):
        assert getattr(cpe, "__deprecated__", "").startswith("Deprecated: use CpeGatewayDevice")
    assert "Deprecated: use CpeGatewayDevice" in (cpe.__doc__ or "")
    assert protocol_attrs(cpe) >= {
        "tr069_client",
        "device_management",
        "hw_console",
        "ntp_client",
        "wifi_rf",
        "network_probe",
    }


def test_reexported() -> None:
    import testprotocols

    for name in (
        "CpeGatewayDevice",
        "CpeGatewayMeshTier",
        "CpeGatewayUspTier",
    ):
        assert name in testprotocols.__all__
        assert hasattr(testprotocols, name)


def test_voice_tier_is_staged_not_built() -> None:
    """The voice tier is `tier-staged` (design §4, §12 M3 and M32): no tier Protocol, no
    capability Protocol and no gateway voice records are published."""
    import importlib.util

    import testprotocols
    import testprotocols.devices.cpe_gateway as gateway
    import testprotocols.models as models
    from testprotocols.models import voice

    assert not hasattr(gateway, "CpeGatewayVoiceTier")
    assert importlib.util.find_spec("testprotocols.voice_gateway") is None
    for name in ("CpeGatewayVoiceTier", "VoiceGateway"):
        assert name not in testprotocols.__all__
    for name in (
        "SipRegistrationState",
        "FxsHookState",
        "SipAccount",
        "SipRegistration",
        "FxsLine",
    ):
        assert not hasattr(voice, name)
        assert name not in models.__all__
