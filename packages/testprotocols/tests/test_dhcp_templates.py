"""Tests for the DhcpClient and DhcpServer Protocol shapes."""

from __future__ import annotations

from testprotocols.dhcp_client import DhcpClient
from testprotocols.dhcp_server import DhcpServer
from testprotocols.models.dhcp import DhcpLeaseObservation

# ---------------------------------------------------------------------------
# DhcpClient
# ---------------------------------------------------------------------------


def test_dhcp_client_is_runtime_checkable() -> None:
    assert getattr(DhcpClient, "_is_runtime_protocol", False)


def test_dhcp_client_protocol_shape() -> None:
    """DhcpClient declares the expected method set."""
    expected = {
        "release_dhcp",
        "renew_dhcp",
        "release_ipv6",
        "renew_ipv6",
        "observe_lease",
        "release_observed_lease",
    }
    actual = set(DhcpClient.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"


def test_dhcp_lease_observation_defaults() -> None:
    """Only the address is mandatory; every other field has an empty default."""
    obs = DhcpLeaseObservation(address="192.0.2.10")
    assert obs.address == "192.0.2.10"
    assert obs.subnet_mask == ""
    assert obs.gateway == ""
    assert obs.dns_servers == ()
    assert obs.lease_time_s == 0
    assert obs.server == ""
    assert dict(obs.options) == {}


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
