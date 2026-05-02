"""WiFi / WifiStations template.

Defines the abstract contract for the AP-side view of associated stations:
enumeration, per-station stats and capability inspection, and admin-driven
disconnect.

Stations are identified by MAC address. The MAC argument format is
free-form on input (drivers normalize); the canonical form returned in
read methods is lowercase colon-separated (e.g. "aa:bb:cc:dd:ee:ff").

Per-frame 802.11v BTM and 802.11k Neighbor-Report-Request operations
live on the WifiTransitions template, not here. This template only
covers admin-state operations on the AP's view of its stations.

Per-BSS MAC ACL administration (set_acl_mode, add_acl_entry, etc.)
lives on the WifiBss template — see SPLITS.md for the rationale.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.wifi import WifiStation


@runtime_checkable
class WifiStations(Protocol):
    """Abstract contract for AP-side WiFi station inspection and admin."""

    # --- Inspection ---

    def list_associated_stations(self, bss_name: str | None = None) -> list[WifiStation]:
        """Return all currently associated stations, optionally filtered to *bss_name*.

        With *bss_name* None, returns stations across all BSSes on the device.
        Raises KeyError if *bss_name* is provided and not registered in WifiBss.
        """
        ...

    def get_station(self, mac: str) -> WifiStation:
        """Return the full record for the associated station identified by *mac*.

        Raises KeyError if no station with that MAC is currently associated.
        """
        ...

    # --- Admin disconnect ---

    def disconnect_station(self, mac: str, reason_code: int | None = None) -> None:
        """Administratively disconnect the station identified by *mac*.

        *reason_code* is an optional IEEE 802.11 reason code (e.g. 1
        "unspecified", 4 "disassociated due to inactivity"). When None the
        driver picks a sensible default. This is admin-state disconnect —
        for an explicit deauth frame use ``WifiTransitions.send_deauth``.

        Raises KeyError if no station with that MAC is currently associated.
        """
        ...
