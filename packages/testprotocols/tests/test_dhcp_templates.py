"""Tests for the DhcpClient and DhcpServer Protocol shapes."""

from __future__ import annotations

from testprotocols.dhcp_client import DhcpClient
from testprotocols.dhcp_server import DhcpServer

# ---------------------------------------------------------------------------
# DhcpClient
# ---------------------------------------------------------------------------


def test_dhcp_client_is_runtime_checkable() -> None:
    assert getattr(DhcpClient, "_is_runtime_protocol", False)


def test_dhcp_client_protocol_shape() -> None:
    """DhcpClient declares the expected method set."""
    expected = {"release_dhcp", "renew_dhcp", "release_ipv6", "renew_ipv6"}
    actual = set(DhcpClient.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"


# ---------------------------------------------------------------------------
# DhcpServer
# ---------------------------------------------------------------------------


def test_dhcp_server_is_runtime_checkable() -> None:
    assert getattr(DhcpServer, "_is_runtime_protocol", False)


def test_dhcp_server_protocol_shape() -> None:
    """DhcpServer declares the expected method set."""
    expected = {"provision_cpe"}
    actual = set(DhcpServer.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"
