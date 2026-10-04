"""Traffic generation specification and result data models."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import cast, override

from testprotocols.deprecation import MODEL_FRAMES, coerce_enum
from testprotocols.models import _checks


class TransportProtocol(StrEnum):
    """The transport a generated traffic stream uses."""

    TCP = "tcp"
    UDP = "udp"


@dataclass
class TrafficSpec:
    """Holds parameters for a traffic generation run (destination, bandwidth, protocol, etc.).

    *protocol* is a :class:`TransportProtocol`. A plain ``str`` naming a member
    (``"udp"``) is deprecated: it warns and converts, also on assignment, so a reader
    holds the enum (it still compares equal to its text); any other string raises
    ``ValueError``.
    """

    destination: str
    bandwidth_mbps: float
    protocol: TransportProtocol | str = TransportProtocol.UDP
    dscp: int = 0
    duration_s: int = 30
    parallel_streams: int = 1
    port: int | None = None

    @override
    def __setattr__(self, name: str, value: object) -> None:
        if name == "protocol":
            value = coerce_enum(
                TransportProtocol,
                cast("TransportProtocol | str", value),
                what="TrafficSpec.protocol",
                skip_file_prefixes=MODEL_FRAMES,
            )
        object.__setattr__(self, name, value)


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
    """A started iperf process: its *pid* and the *log_file* its output goes to (the path
    ``get_iperf_logs`` reads). :meth:`as_tuple` is the released ``(pid, log_file)`` return of
    ``start_traffic_sender`` / ``start_traffic_receiver``."""

    pid: int
    log_file: str

    def __post_init__(self) -> None:
        _checks.count("IperfProcess", "pid", self.pid)
        if self.pid == 0:
            raise ValueError("IperfProcess.pid must be positive: 0")
        _checks.text("IperfProcess", "log_file", self.log_file)
        if not self.log_file:
            raise ValueError("IperfProcess.log_file must name a file: ''")

    def as_tuple(self) -> tuple[int, str]:
        """The released ``(pid, log_file)`` pair."""
        return self.pid, self.log_file


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
