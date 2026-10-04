"""IP / Routing template.

Defines the abstract contract for IP routing operations such as ping, traceroute,
and default gateway management.
"""

from __future__ import annotations

from ipaddress import IPv4Address
from typing import Any, Protocol, runtime_checkable

from testprotocols.models.networking import PingResult


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
        """Send ICMP echo requests to *ping_ip* and return success or parsed output.

        *options* is deprecated with no typed replacement: no caller was seen to pass one
        through this member. A driver warns when it is non-empty.

        Returns ``True`` when every request was answered. With ``json_output=True`` it
        returns the tool's parsed output instead; that form is deprecated: use
        :meth:`ping_stats`, which returns a typed summary (a driver warns when
        ``json_output`` is true, and keeps its released parsed output until the removal
        step, since that output carries more than the summary holds).
        """
        ...

    def ping_stats(
        self,
        ping_ip: str,
        ping_count: int = 4,
        ping_interface: str | None = None,
        timeout: int = 50,
    ) -> PingResult:
        """Send *ping_count* ICMP echo requests to *ping_ip* (from *ping_interface* when
        given, waiting up to *timeout* seconds) and return the run's summary."""
        ...

    def traceroute(
        self,
        host_ip: str | IPv4Address,
        version: str = "",
        options: str = "",
        timeout: int = 60,
    ) -> str | None:
        """Run a traceroute to *host_ip* and return the output.

        *options* is deprecated with no typed replacement: no caller was seen to pass one. A
        driver warns when it is non-empty.

        *version* is the suffix of the command name: ``""`` (the default) runs
        ``traceroute`` and ``"6"`` runs ``traceroute6``. It stays ``str`` because the released
        implementers declare ``str``; it narrows to
        :class:`~testprotocols.models.IpFamily` ``| None`` (``None`` for the default) in a
        later release.
        """
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
