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

    def ping(  # type: ignore[explicit-any]  # released signature kept until removal
        self,
        ping_ip: str,
        ping_count: int = 4,
        ping_interface: str | None = None,
        options: str = "",
        timeout: int = 50,
        json_output: bool = False,
    ) -> bool | dict[str, Any]:
        """Send ICMP echo requests to *ping_ip* and return success or parsed output.

        Returns ``True`` when every request was answered. With ``json_output=True`` it
        returns the tool's parsed output instead.

        Deprecated: the *options* parameter, with no typed replacement: no caller was seen to
        pass one through this member. Removal not before the first release 6 months after the
        release that deprecates it.

        Deprecated: ``json_output=True``; use :meth:`ping_stats`, which returns a typed summary
        (the released parsed output carries more than the summary holds). At removal ``ping``
        returns ``bool``. Removal not before the first release 6 months after the release that
        deprecates it.
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

        *version* is the suffix of the command name: ``""`` (the default) runs
        ``traceroute`` and ``"6"`` runs ``traceroute6``. It stays ``str`` because the released
        implementers declare ``str``.

        Deprecated: the *options* parameter, with no typed replacement: no caller was seen to
        pass one. Removal not before the first release 6 months after the release that
        deprecates it.

        Deprecated: *version* as ``str``; it narrows to
        :class:`~testprotocols.models.IpFamily` ``| None`` (``None`` for the default). Removal
        not before the first release 6 months after the release that deprecates it.
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
