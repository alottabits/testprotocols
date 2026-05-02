"""IP / Routing template.

Defines the abstract contract for IP routing operations such as ping, traceroute,
and default gateway management.
"""

from __future__ import annotations

from ipaddress import IPv4Address
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IpRouting(Protocol):
    """Abstract contract for IP routing operations."""

    def ping(
        self,
        ping_ip: str,
        ping_count: int = 4,
        ping_interface: str | None = None,
        options: str = "",
        timeout: int = 50,
        json_output: bool = False,
    ) -> bool | dict[str, Any]:
        """Send ICMP echo requests to *ping_ip* and return success or parsed output."""
        ...

    def traceroute(
        self,
        host_ip: str | IPv4Address,
        version: str = "",
        options: str = "",
        timeout: int = 60,
    ) -> str | None:
        """Run a traceroute to *host_ip* and return the output."""
        ...

    def add_route(self, destination: str, gw_interface: str) -> None:
        """Add a static route to *destination* via *gw_interface*."""
        ...

    def delete_route(self, destination: str) -> None:
        """Delete the static route to *destination*."""
        ...

    def get_default_gateway(self) -> IPv4Address:
        """Return the current default gateway address."""
        ...

    def del_default_route(self, interface: str | None = None) -> None:
        """Delete the default route, optionally scoped to *interface*."""
        ...

    def set_default_gw(self, ip_address: IPv4Address, interface: str) -> None:
        """Set the default gateway to *ip_address* via *interface*."""
        ...
