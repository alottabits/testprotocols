"""Tests for the testprotocols package's __init__.py re-exports."""

from __future__ import annotations

import testprotocols


def test_all_exports_importable() -> None:
    """Every name listed in ``__all__`` must be a real attribute on the package."""
    for name in testprotocols.__all__:
        assert hasattr(testprotocols, name), f"Missing export: {name}"


def test_capability_protocols_re_exported() -> None:
    """The eight capability Protocols are re-exported at the top level."""
    expected = {
        "FirewallZones",
        "IpInterface",
        "IpRouting",
        "NetemController",
        "SipPhone",
        "SipServer",
        "Tr069Client",
        "Tr069Server",
    }
    assert expected <= set(testprotocols.__all__)


def test_device_archetypes_re_exported() -> None:
    """The 13 device-archetype Protocols are re-exported at the top level."""
    expected = {
        "AcsDevice",
        "CpeDevice",
        "IperfTrafficGeneratorDevice",
        "LanClientDevice",
        "ProvisionerDevice",
        "QoeClientDevice",
        "SdwanRouterDevice",
        "SipPhoneDevice",
        "SipServerDevice",
        "TftpDevice",
        "TrafficControllerDevice",
        "WanServerDevice",
        "WlanClientDevice",
    }
    assert expected <= set(testprotocols.__all__)
