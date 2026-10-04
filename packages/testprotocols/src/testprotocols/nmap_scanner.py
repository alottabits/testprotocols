"""Nmap / Scanner template.

Defines the abstract contract for network scanning operations using nmap.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from testprotocols.models.networking import IpVersion, NmapResult
from testprotocols.models.ports import PortRange
from testprotocols.models.traffic import TransportProtocol


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
        """Deprecated: use :meth:`scan`, which returns a typed result.

        Runs an nmap scan against *ipaddr* and returns the parsed results. A driver keeps its
        released output here until the removal step (it warns with
        ``warn_renamed("nmap", "scan")``): drivers return differently shaped trees, which a
        typed result cannot reproduce.

        *ip_type* is an :class:`~testprotocols.models.IpVersion` (``"ipv4"`` or
        ``"ipv6"``; a released implementer raises ``ValueError`` for any other word). A
        plain ``str`` naming a member is deprecated: the driver converts it and warns.
        *protocol* stays free text: it is the scan-type option the tool is given
        (``"-sU"``), not an IP protocol.
        """
        ...

    def scan(
        self,
        target: str,
        ip_version: IpVersion,
        *,
        ports: Sequence[PortRange] = (),
        protocol: TransportProtocol | None = None,
        max_retries: int | None = None,
        min_rate: int | None = None,
        timeout: int = 30,
    ) -> NmapResult:
        """Port-scan *target* (an address or host name) over *ip_version* and return what
        was found.

        *ports* are the ranges to scan (``()``: the tool's default set); *protocol* the
        transport to scan (``None``: the tool's default, TCP); *max_retries* caps probe
        retransmissions and *min_rate* sets the minimum probe rate (packets per second);
        *timeout* is in seconds.
        """
        ...
