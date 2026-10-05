"""Traffic generation specification and result data models."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import cast


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
    protocol: TransportProtocol | str = TransportProtocol.UDP
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


_SIZE = re.compile(r"\s*([0-9]+(?:\.[0-9]+)?)([kKmMgGtT]?)\s*")
_SIZE_UNITS = {"": 1, "k": 1024, "m": 1024**2, "g": 1024**3, "t": 1024**4}


def parse_window_size(text: str) -> int:
    """Return an iperf size option (``"8M"``, ``"512K"``, ``"65536"``) as a byte count.

    The grammar is iperf's: a decimal number, optionally with a fraction, and an optional
    suffix ``K``, ``M``, ``G`` or ``T`` (either case) in binary units (``K`` = 1024). A
    fractional result is truncated, as iperf does. Text that is not such a size, or that
    gives zero, raises ``ValueError``; a non-text value raises ``TypeError``.
    """
    if not isinstance(cast(object, text), str):
        raise TypeError(f"window size: takes text, not {text!r}")
    match = _SIZE.fullmatch(text)
    if match is None:
        raise ValueError(f"window size: {text!r} is not a size such as '8M'")
    number, unit = match.groups()
    size = int(Decimal(number) * _SIZE_UNITS[unit.lower()])
    if size <= 0:
        raise ValueError(f"window size: {text!r} is not a positive size")
    return size
