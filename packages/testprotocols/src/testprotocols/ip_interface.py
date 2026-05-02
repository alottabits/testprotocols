"""IP / Interface template.

Defines the abstract contract for querying and configuring IP interface state.
"""

from __future__ import annotations

from ipaddress import IPv4Address
from typing import Protocol, runtime_checkable


@runtime_checkable
class IpInterface(Protocol):
    """Abstract contract for IP interface operations."""

    def get_interface_ipv4addr(self, interface: str) -> str:
        """Return the IPv4 address assigned to *interface*."""
        ...

    def get_interface_ipv6addr(self, interface: str) -> str:
        """Return the global IPv6 address assigned to *interface*."""
        ...

    def get_interface_link_local_ipv6addr(self, interface: str) -> str:
        """Return the link-local IPv6 address of *interface*."""
        ...

    def get_interface_macaddr(self, interface: str) -> str:
        """Return the MAC address of *interface*."""
        ...

    def get_interface_mask(self, interface: str) -> str:
        """Return the subnet mask of *interface*."""
        ...

    def get_interface_mtu_size(self, interface: str) -> int:
        """Return the MTU size of *interface*."""
        ...

    def is_link_up(self, interface: str, pattern: str = "BROADCAST,MULTICAST,UP") -> bool:
        """Return True if *interface* flags match *pattern*."""
        ...

    def set_link_state(self, interface: str, state: str) -> None:
        """Bring *interface* up or down according to *state*."""
        ...

    def enable_ipv6(self) -> None:
        """Enable IPv6 on the device."""
        ...

    def disable_ipv6(self) -> None:
        """Disable IPv6 on the device."""
        ...

    def set_static_ip(self, interface: str, ip_address: IPv4Address, netmask: IPv4Address) -> None:
        """Assign a static IP address and netmask to *interface*."""
        ...

    def remove_static_ip(self, interface: str) -> None:
        """Remove any static IP address configuration from *interface*."""
        ...
