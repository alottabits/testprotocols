"""Nmap / Scanner template.

Defines the abstract contract for network scanning operations using nmap.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from testprotocols._compat import deprecated
from testprotocols.models.networking import IpFamily, IpVersion, NmapResult
from testprotocols.models.ports import PortRange
from testprotocols.models.traffic import TransportProtocol


@runtime_checkable
class NmapScanner(Protocol):
    """Abstract contract for nmap network scanning operations."""

    @deprecated(
        "Deprecated: use scan_ports. Removal not before the first release 6 months "
        "after the release that deprecates it.",
        category=None,
    )
    def nmap(  # type: ignore[explicit-any]  # released signature kept until removal
        self,
        ipaddr: str,
        ip_type: IpVersion | str,
        port: str | int | None = None,
        protocol: str | None = None,
        max_retries: int | None = None,
        min_rate: int | None = None,
        opts: str | None = None,
        timeout: int = 30,
        *,
        fast: bool = False,
    ) -> dict[str, Any]:
        """Run an nmap scan against *ipaddr* and return the parsed results.

        Drivers return differently shaped trees, which the typed result of
        :meth:`scan_ports` cannot reproduce.

        *ip_type* is an :class:`~testprotocols.models.IpVersion` (``"ipv4"`` or
        ``"ipv6"``; a released implementer raises ``ValueError`` for any other word).
        *protocol* stays free text: it is the scan-type option the tool is given
        (``"-sU"``), not an IP protocol.

        *fast* scans fewer ports than the tool's default set. It replaces the released *opts*
        string, which goes with this member; giving both raises ``ValueError``.

        Deprecated: use :meth:`scan_ports`. Removal not before the first release 6 months after the
        release that deprecates it.
        """
        ...

    def scan_ports(
        self,
        target: str,
        ip_version: IpFamily,
        *,
        ports: Sequence[PortRange] = (),
        protocol: TransportProtocol | None = None,
        max_retries: int | None = None,
        min_rate: int | None = None,
        timeout: int = 30,
        fast: bool = False,
    ) -> NmapResult:
        """Port-scan *target* (an address or host name) over *ip_version*
        (:class:`~testprotocols.models.IpFamily`) and return what was found.

        *ports* are the ranges to scan (``()``: the tool's default set); *protocol* the
        transport to scan (``None``: the tool's default, TCP); *max_retries* caps probe
        retransmissions and *min_rate* sets the minimum probe rate (packets per second);
        *timeout* is in seconds; *fast* scans fewer ports than the default set (an explicit
        *ports* wins).
        """
        ...
