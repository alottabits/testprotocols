"""Traffic / QoeBrowser template.

Defines the abstract contract for browser-based Quality of Experience (QoE)
measurement operations.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.qoe import MeasurementSpec, QoEResult


@runtime_checkable
class QoeBrowser(Protocol):
    """Abstract contract for browser-based QoE measurement."""

    def measure(self, url: str, spec: MeasurementSpec) -> QoEResult:
        """Run a generic QoE measurement against *url* using *spec*."""
        ...

    def measure_productivity(
        self,
        url: str,
        *,
        spec: MeasurementSpec | None = None,
        scenario: str = "page_load",
        wait_until: str = "networkidle",
        timeout_ms: int = 30000,
        force_quic: bool = True,
    ) -> QoEResult:
        """Measure productivity-app QoE for *url* (e.g., page-load time).

        ``force_quic=True`` (default) forces HTTP/3/QUIC, as a QoE measurement
        should. Set ``force_quic=False`` for a reachability/block probe: the
        navigation runs over TCP/h2 (QUIC disabled), so a non-HTTP/3 site stays
        reachable and a TCP/TLS-inspecting middlebox (e.g. content filtering)
        actually sees the traffic.
        """
        ...

    def measure_streaming(
        self,
        stream_url: str,
        *,
        spec: MeasurementSpec | None = None,
        duration_s: int = 30,
    ) -> QoEResult:
        """Measure streaming QoE for *stream_url* over *duration_s* seconds."""
        ...

    def measure_conferencing(
        self,
        session_url: str,
        *,
        spec: MeasurementSpec | None = None,
        duration_s: int = 60,
    ) -> QoEResult:
        """Measure conferencing QoE for *session_url* over *duration_s* seconds."""
        ...

    def attempt_outbound_connection(
        self,
        host: str,
        port: int,
        *,
        timeout_s: float = 5.0,
    ) -> bool:
        """Attempt a TCP connection to *host*:*port* and return True if successful."""
        ...
