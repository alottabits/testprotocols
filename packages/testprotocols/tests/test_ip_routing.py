"""Tests for the IpRouting Protocol shape."""

from __future__ import annotations

from testprotocols.ip_routing import IpRouting


def test_ip_routing_is_runtime_checkable() -> None:
    assert getattr(IpRouting, "_is_runtime_protocol", False)


def test_ip_routing_protocol_shape() -> None:
    """IpRouting declares the expected method set."""
    expected = {
        "ping",
        "traceroute",
        "add_route",
        "delete_route",
        "get_default_gateway",
        "del_default_route",
        "set_default_gw",
    }
    actual = set(IpRouting.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"
