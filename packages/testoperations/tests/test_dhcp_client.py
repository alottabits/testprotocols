"""Tests for testoperations.dhcp_client module."""

from __future__ import annotations

from unittest.mock import MagicMock

from testoperations.dhcp_client import (
    dhcp_renew_ipv4,
    dhcp_renew_stateful_ipv6,
    dhcp_renew_stateless_ipv6,
)

# ---------------------------------------------------------------------------
# dhcp_renew_ipv4
# ---------------------------------------------------------------------------


class TestDhcpRenewIpv4:
    def test_releases_and_renews(self):
        dhcp = MagicMock()
        ip = MagicMock()
        ip.get_interface_ipv4addr.return_value = "192.168.1.100"

        result = dhcp_renew_ipv4(dhcp, ip, "eth1")

        dhcp.release_dhcp.assert_called_once_with("eth1")
        dhcp.renew_dhcp.assert_called_once_with("eth1")
        ip.get_interface_ipv4addr.assert_called_once_with("eth1")
        assert result == "192.168.1.100"

    def test_returns_new_ip(self):
        dhcp = MagicMock()
        ip = MagicMock()
        ip.get_interface_ipv4addr.return_value = "10.0.0.50"

        result = dhcp_renew_ipv4(dhcp, ip, "eth0")
        assert result == "10.0.0.50"


# ---------------------------------------------------------------------------
# dhcp_renew_stateful_ipv6
# ---------------------------------------------------------------------------


class TestDhcpRenewStatefulIpv6:
    def test_releases_and_renews_ipv6(self):
        dhcp = MagicMock()
        ip = MagicMock()
        ip.get_interface_ipv6addr.return_value = "2001:db8::1"

        result = dhcp_renew_stateful_ipv6(dhcp, ip, "eth1")

        dhcp.release_ipv6.assert_called_once_with("eth1")
        dhcp.renew_ipv6.assert_called_once_with("eth1")
        ip.get_interface_ipv6addr.assert_called_once_with("eth1")
        assert result == "2001:db8::1"


# ---------------------------------------------------------------------------
# dhcp_renew_stateless_ipv6
# ---------------------------------------------------------------------------


class TestDhcpRenewStatelessIpv6:
    def test_renews_with_stateless_flag(self):
        dhcp = MagicMock()
        ip = MagicMock()
        ip.get_interface_ipv6addr.return_value = "fe80::1"

        result = dhcp_renew_stateless_ipv6(dhcp, ip, "eth1")

        dhcp.release_ipv6.assert_called_once_with("eth1", stateless=True)
        dhcp.renew_ipv6.assert_called_once_with("eth1", stateless=True)
        ip.get_interface_ipv6addr.assert_called_once_with("eth1")
        assert result == "fe80::1"
