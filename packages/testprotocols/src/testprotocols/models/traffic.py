"""Traffic generation specification and result data models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import cast, override

from testprotocols.deprecation import MODEL_FRAMES, coerce_enum


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
