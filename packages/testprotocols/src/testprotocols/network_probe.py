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
