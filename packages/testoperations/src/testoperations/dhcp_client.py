"""DHCP client operations — compose dhcp_client + ip_interface templates.

These functions orchestrate DHCP lease renewal by delegating to the
``dhcp_client`` and ``ip_interface`` template instances provided by the caller.
"""

from __future__ import annotations

from testprotocols.dhcp_client import DhcpClient
from testprotocols.ip_interface import IpInterface


def dhcp_renew_ipv4(dhcp_client: DhcpClient, ip_interface: IpInterface, iface: str) -> str:
    """Release and renew the DHCPv4 lease, return the new IPv4 address."""
    dhcp_client.release_dhcp(iface)
    dhcp_client.renew_dhcp(iface)
    return ip_interface.get_interface_ipv4addr(iface)


def dhcp_renew_stateful_ipv6(dhcp_client: DhcpClient, ip_interface: IpInterface, iface: str) -> str:
    """Release and renew the stateful DHCPv6 lease, return the new IPv6 address."""
    dhcp_client.release_ipv6(iface)
    dhcp_client.renew_ipv6(iface)
    return ip_interface.get_interface_ipv6addr(iface)


def dhcp_renew_stateless_ipv6(
    dhcp_client: DhcpClient, ip_interface: IpInterface, iface: str
) -> str:
    """Release and renew the stateless (SLAAC/DHCPv6-PD) IPv6 configuration,
    return the new IPv6 address."""
    dhcp_client.release_ipv6(iface, stateless=True)
    dhcp_client.renew_ipv6(iface, stateless=True)
    return ip_interface.get_interface_ipv6addr(iface)
