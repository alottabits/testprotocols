"""Nmap / Scanner template.

Defines the abstract contract for network scanning operations using nmap.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from testprotocols.models.networking import IpVersion


@runtime_checkable
class NmapScanner(Protocol):
    """Abstract contract for nmap network scanning operations."""

    def nmap(
        self,
        ipaddr: str,
        ip_type: IpVersion | str,
        port: str | int | None = None,
        protocol: str | None = None,
        max_retries: int | None = None,
        min_rate: int | None = None,
        opts: str | None = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Run an nmap scan against *ipaddr* and return the parsed results.

        *ip_type* is an :class:`~testprotocols.models.IpVersion` (``"ipv4"`` or
        ``"ipv6"``; a released implementer raises ``ValueError`` for any other word). A
        plain ``str`` naming a member is deprecated: the driver converts it and warns.
        *protocol* stays free text: it is the scan-type option the tool is given
        (``"-sU"``), not an IP protocol.
        """
        ...
