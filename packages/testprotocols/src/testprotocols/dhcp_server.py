"""DHCP / Server template.

Defines the abstract contract for DHCP server operations such as CPE
provisioning.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DhcpServer(Protocol):
    """Abstract contract for DHCP server operations."""

    def provision_cpe(
        self,
        cpe_mac: str,
        dhcpv4_options: dict[str, Any],
        dhcpv6_options: dict[str, Any],
    ) -> None:
        """Provision a CPE device by MAC address with the given DHCP options."""
        ...
