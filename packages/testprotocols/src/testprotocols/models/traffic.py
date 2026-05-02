"""Traffic generation specification and result data models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TrafficSpec:
    """Holds parameters for a traffic generation run (destination, bandwidth, protocol, etc.)."""

    destination: str
    bandwidth_mbps: float
    protocol: str = "udp"
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
