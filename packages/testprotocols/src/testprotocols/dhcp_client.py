"""DHCP / Client template.

Defines the abstract contract for DHCP client operations including lease
release and renewal for both IPv4 and IPv6.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class DhcpClient(Protocol):
    """Abstract contract for DHCP client operations."""

    def release_dhcp(self, interface: str) -> None:
        """Release the DHCPv4 lease on *interface*."""
        ...

    def renew_dhcp(self, interface: str) -> None:
        """Renew the DHCPv4 lease on *interface*."""
        ...

    def release_ipv6(self, interface: str, stateless: bool = False) -> None:
        """Release the DHCPv6 lease on *interface*."""
        ...

    def renew_ipv6(self, interface: str, stateless: bool = False) -> None:
        """Renew the DHCPv6 lease on *interface*."""
        ...
