"""WiFi / WifiRf template.

Defines the abstract contract for per-radio RF observability:
on-demand scan triggering, neighbor BSS enumeration, channel utilization,
noise floor, and cumulative per-radio TX/RX/retry counters.

Read-only telemetry only — PHY configuration (channel, bandwidth, tx
power, mode, country, DFS state) lives in WifiRadio. Per-frame 802.11
spectrum analysis (FFT, CleanAir, spectral_scan) is deferred to a future
WifiSpectrum template, given the low cross-vendor uniformity.

Per-radio identity is band-keyed, matching WifiRadio.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.wifi import (
    WifiChannelUtilization,
    WifiNeighbor,
    WifiRadioStats,
)


@runtime_checkable
class WifiRf(Protocol):
    """Abstract contract for per-radio WiFi RF telemetry."""

    # --- Scan ---

    def scan(self, band: str, timeout: float = 30.0) -> list[WifiNeighbor]:
        """Trigger an off-channel scan on *band* and return the neighbour BSSes found.

        Blocks until scan results are available or *timeout* seconds elapse.
        Hides vendor divergence:
        - Vendors that return immediately with a job handle: the driver polls
          the job until it completes.
        - Vendors that return inline: the driver returns directly.
        - Vendors that post results to a separate diagnostic resource: the
          driver polls that resource.

        Raises TimeoutError if results are not available within *timeout*.
        """
        ...

    def get_neighbors(self, band: str) -> list[WifiNeighbor]:
        """Return the most recent neighbour-BSS list for *band* without triggering a new scan.

        Returns whatever the driver has cached from prior background scans
        or the most recent ``scan()`` call. Empty list if no scan has run.
        """
        ...

    # --- Channel telemetry ---

    def get_channel_utilization(self, band: str) -> WifiChannelUtilization:
        """Return current channel utilization breakdown for *band*.

        All percentages are 0-100. Drivers that don't separate TX/RX/interference
        components return only ``busy_pct`` populated; the others are None.
        """
        ...

    def get_noise_floor(self, band: str) -> int:
        """Return the current noise floor on *band* in dBm (typically negative, e.g. -95)."""
        ...

    # --- Cumulative per-radio counters ---

    def get_radio_stats(self, band: str) -> WifiRadioStats:
        """Return cumulative per-radio TX/RX/retry counters for *band*.

        Counters are since the radio came up (typically boot or last
        ``WifiRadio.set_enabled(band, True)``). Drivers reset them on
        radio disable/enable cycles.
        """
        ...
