"""Quality of Experience (QoE) result and measurement specification models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QoEResult:
    """Holds QoE metrics measured during a test (latency, jitter, MOS, etc.)."""

    ttfb_ms: float | None = None
    load_time_ms: float | None = None
    startup_time_ms: float | None = None
    rebuffer_ratio: float | None = None
    latency_ms: float | None = None
    jitter_ms: float | None = None
    packet_loss_pct: float | None = None
    mos_score: float | None = None
    protocol: str | None = None
    success: bool = True


@dataclass
class MeasurementSpec:
    """Holds parameters controlling how a QoE measurement is performed."""

    tool: str = "browser"
    completion: str = "networkidle"
    timeout_ms: int = 30000
    duration_s: int | None = None
    force_quic: bool = True
