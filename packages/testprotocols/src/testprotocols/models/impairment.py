"""Network impairment profile data model and transient impairment events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass
class ImpairmentProfile:
    """Holds parameters describing a network impairment scenario (latency, jitter, loss, etc.)."""

    latency_ms: int
    jitter_ms: int
    loss_percent: float
    bandwidth_limit_mbps: int | None = None
    reorder_percent: float = 0.0
    corrupt_percent: float = 0.0
    duplicate_percent: float = 0.0


@dataclass(frozen=True)
class Blackout:
    """Every packet is lost for the event's duration (100 % loss); the latency and jitter
    in force are kept."""

    event_name: ClassVar[str] = "blackout"


@dataclass(frozen=True)
class Brownout:
    """A degraded link: the given one-way *latency_ms* and *jitter_ms* (not negative) and
    *loss_percent* (0 to 100). A field left ``None`` takes the driver's own default for a
    brownout."""

    event_name: ClassVar[str] = "brownout"

    latency_ms: int | None = None
    jitter_ms: int | None = None
    loss_percent: float | None = None


@dataclass(frozen=True)
class LatencySpike:
    """A temporary high latency: *latency_ms* (one-way) and *jitter_ms* during the spike,
    not negative; the loss in force is kept. A field left ``None`` takes the driver's own
    default."""

    event_name: ClassVar[str] = "latency_spike"

    latency_ms: int | None = None
    jitter_ms: int | None = None


@dataclass(frozen=True)
class PacketStorm:
    """A burst of packet loss: *loss_percent* (0 to 100) with the given *latency_ms* and
    *jitter_ms* (not negative), as the released implementers apply a packet storm. A field
    left ``None`` takes the driver's own default.

    *duplicate_percent* (0 to 100) is optional and ``None`` (not requested) by default: the
    share of packets duplicated as well. No released implementer applies duplication; a
    driver that cannot apply a requested field raises ``ValueError`` rather than ignoring
    it."""

    event_name: ClassVar[str] = "packet_storm"

    loss_percent: float | None = None
    latency_ms: int | None = None
    jitter_ms: int | None = None
    duplicate_percent: float | None = None


TransientEvent = Blackout | Brownout | LatencySpike | PacketStorm
"""A timed impairment event for ``NetemController.inject_event``. Each event's
``event_name`` is its released ``inject_transient`` word."""
