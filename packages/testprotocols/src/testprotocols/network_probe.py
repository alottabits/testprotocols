"""Network reachability probe template.

Defines the abstract contract for L3/L4 reachability checks initiated from
a host toward an external target. Distinct from ``HttpClient`` (which is
app-layer): a ``NetworkProbe`` verifies whether the SYN/ACK handshake
completes, not whether an HTTP responder is configured at the far end.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class NetworkProbe(Protocol):
    """Abstract contract for L3/L4 reachability probes."""

    def tcp_can_connect(self, host: str, port: int, timeout: int = 5) -> bool:
        """Attempt a TCP connection to *host*:*port* and return reachability.

        Returns ``True`` if the three-way handshake completes within
        *timeout* seconds, ``False`` otherwise (connection refused, no
        route, filtered, timed out). The probe is read-only — no data is
        sent on the connection — so it is safe to call against arbitrary
        targets without side effects on the destination.
        """
        ...

    def icmp_can_reach(self, host: str, count: int = 1, timeout: int = 5) -> bool:
        """Attempt an ICMP echo to *host* and return reachability.

        Returns ``True`` if at least one of *count* echo requests is answered
        within *timeout* seconds, ``False`` otherwise (no route, filtered,
        timed out). Read-only — echo requests have no side effect on the
        destination.
        """
        ...

    def udp_can_reach(self, host: str, port: int, timeout: int = 5) -> bool:
        """Attempt a UDP exchange with *host*:*port* and return reachability.

        UDP is connectionless and has no handshake, so a dropped datagram is
        indistinguishable from a delivered one at the sender unless the far end
        replies. This probe therefore reports reachability based on a **reply**
        from a UDP responder at the target within *timeout* seconds — callers
        that need a definitive verdict must ensure a responder is present. A
        missing reply (no responder, no route, or filtered) is ``False``.
        """
        ...
