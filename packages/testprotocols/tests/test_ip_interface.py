"""Tests for the IpInterface Protocol shape."""

from __future__ import annotations

from testprotocols.ip_interface import IpInterface


def test_ip_interface_is_runtime_checkable() -> None:
    assert getattr(IpInterface, "_is_runtime_protocol", False)


def test_ip_interface_protocol_shape() -> None:
    """IpInterface declares the expected method set."""
    expected = {
        "get_interface_ipv4addr",
        "get_interface_ipv6addr",
        "get_interface_link_local_ipv6addr",
        "get_interface_macaddr",
        "get_interface_mask",
        "get_interface_mtu_size",
        "set_interface_mtu_size",
        "is_link_up",
        "set_link_state",
        "enable_ipv6",
        "disable_ipv6",
        "set_static_ip",
        "remove_static_ip",
    }
    actual = set(IpInterface.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"
