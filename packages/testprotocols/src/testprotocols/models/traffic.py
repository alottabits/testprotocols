"""Traffic generation specification and result data models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TransportProtocol(StrEnum):
    """The transport a generated traffic stream uses."""

    TCP = "tcp"
    UDP = "udp"


@dataclass
class TrafficSpec:
    """Holds parameters for a traffic generation run (destination, bandwidth, protocol, etc.).

    *protocol* is a :class:`TransportProtocol`. A plain ``str`` naming a member
    (``"udp"``) is deprecated and stored as given (a member compares equal to its
    text); the field narrows to :class:`TransportProtocol` when the plain ``str`` form
    is removed.
    """

    destination: str
    bandwidth_mbps: float
    protocol: TransportProtocol | str = "udp"
    dscp: int = 0
    duration_s: int = 30
    parallel_streams: int = 1
    port: int | None = None


@dataclass
class TrafficResult:
    """Holds measured outcomes from a traffic generation run."""

    sent_mbps: float = 0.0
    received_mbps: float = 0.0
    loss_percent: float = 0.0
    jitter_ms: float | None = None
    dscp_marking: int = 0


@dataclass(frozen=True)
class IperfProcess:
    """A started iperf process: its *pid* (positive) and the *log_file* its output goes to
    (the path ``get_iperf_logs`` reads, not empty)."""

    pid: int
    log_file: str
