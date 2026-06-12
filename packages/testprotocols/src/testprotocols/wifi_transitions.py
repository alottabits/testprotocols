"""WiFi / WifiTransitions template.

Defines the abstract contract for IEEE 802.11k/v/r transition primitives
on a WiFi-capable device:

- Per-BSS admin enable for 802.11k (Radio Resource Management),
  802.11v (BSS Transition Management), and 802.11r (Fast Transition).
- Per-client triggered frames: BTM Request (802.11v), Neighbor Report
  Request (802.11k), explicit deauth.

802.11w (PMF) is set as a security parameter on WifiBss; reading it is
also done via WifiBss (no convenience-bleed snapshot here).

Per-client triggers may legitimately raise NotImplementedError on drivers
whose underlying stack only exposes coarse-grained "client steering"
features without raw frame-send (typical of controller-managed enterprise
stacks).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.wifi import WifiTransitionConfig


@runtime_checkable
class WifiTransitions(Protocol):
    """Abstract contract for 802.11 k/v/r admin and per-client transition primitives."""

    # --- Per-BSS enables ---

    def set_rrm_enabled(self, bss_name: str, enabled: bool) -> None:
        """Enable or disable 802.11k Radio Resource Management on *bss_name*.

        Raises KeyError if *bss_name* is not registered.
        """
        ...

    def set_btm_enabled(self, bss_name: str, enabled: bool) -> None:
        """Enable or disable 802.11v BSS Transition Management on *bss_name*.

        Raises KeyError if *bss_name* is not registered.
        """
        ...

    def set_ft_enabled(self, bss_name: str, enabled: bool, *, over_ds: bool = False) -> None:
        """Enable or disable 802.11r Fast Transition on *bss_name*.

        *over_ds* controls FT-over-the-DS (True) vs FT-over-the-air (False).
        Ignored when *enabled* is False.
        Raises KeyError if *bss_name* is not registered.
        """
        ...

    def get_transition_config(self, bss_name: str) -> WifiTransitionConfig:
        """Return the k/v/r configuration of *bss_name* (single read).

        Raises KeyError if *bss_name* is not registered.
        """
        ...

    # --- Per-client triggers ---

    def send_btm_request(
        self,
        mac: str,
        candidate_bssids: list[str] | None = None,
        *,
        disassoc_imminent: bool = False,
    ) -> None:
        """Send an 802.11v BSS Transition Management Request to the station *mac*.

        *candidate_bssids* is an optional list of preferred candidate BSSIDs
        for the client to consider roaming to (canonical lowercase
        colon-separated). When None, the AP includes its default candidate set.

        *disassoc_imminent* sets the "disassociation imminent" bit in the
        request, prompting the client to roam faster on penalty of being
        disassociated.

        Raises KeyError if no station with that MAC is currently associated.
        Drivers without raw BTM-frame support raise NotImplementedError.
        """
        ...

    def send_neighbor_report_request(self, mac: str) -> None:
        """Send an 802.11k Neighbor Report Request to the station *mac*.

        The client's response (a Neighbor Report containing BSSes it can see)
        is consumed by the driver's internal neighbour table. Tests that
        need the AP-side view of neighbours read it via
        ``WifiRf.get_neighbors``; the per-client client-side neighbour
        report is not modelled in this release.

        Raises KeyError if no station with that MAC is currently associated.
        Drivers without raw 802.11k-NRR support raise NotImplementedError.
        """
        ...

    def send_deauth(self, mac: str, reason_code: int = 2) -> None:
        """Send an explicit IEEE 802.11 Deauthentication frame to the station *mac*.

        *reason_code* is an IEEE 802.11 reason code (default 2 — "previous
        authentication no longer valid"). This is a raw-frame primitive,
        distinct from ``WifiStations.disconnect_station`` which is admin-state
        disconnect.

        Raises KeyError if no station with that MAC is currently associated.
        Drivers without raw deauth-frame support raise NotImplementedError.
        """
        ...
