"""Network impairment profile data model."""
from __future__ import annotations

from dataclasses import dataclass, field


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
