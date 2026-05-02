"""WiFi / WifiStations template.

Defines the abstract contract for the AP-side view of associated stations:
enumeration, per-station stats and capability inspection, admin-driven
disconnect, and per-BSS MAC ACL administration.

Stations are identified by MAC address. The MAC argument format is
free-form on input (drivers normalize); the canonical form returned in
read methods is lowercase colon-separated (e.g. "aa:bb:cc:dd:ee:ff").

Per-frame 802.11v BTM and 802.11k Neighbor-Report-Request operations
live on the WifiTransitions template, not here. This template only
covers admin-state operations on the AP's view of its stations.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.wifi import WifiAcl, WifiStation


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

    # --- MAC ACL — per-BSS access control list ---

    def set_acl_mode(self, bss_name: str, mode: str) -> None:
        """Set the per-BSS MAC ACL mode.

        *mode* is one of:
        - ``"disabled"`` — no MAC filtering; *bss_name*'s ACL list is ignored
        - ``"allow"`` — allow-list (whitelist); only MACs in the ACL may associate
        - ``"deny"`` — deny-list (blacklist); MACs in the ACL are blocked

        Raises KeyError if *bss_name* is not registered.
        """
        ...

    def add_acl_entry(self, bss_name: str, mac: str) -> None:
        """Add *mac* to the BSS's ACL list. No-op if already present.

        Effective filtering depends on the current ACL mode.
        Raises KeyError if *bss_name* is not registered.
        """
        ...

    def remove_acl_entry(self, bss_name: str, mac: str) -> None:
        """Remove *mac* from the BSS's ACL list. No-op if absent.

        Raises KeyError if *bss_name* is not registered.
        """
        ...

    def clear_acl(self, bss_name: str) -> None:
        """Remove all entries from the BSS's ACL list. Mode is unchanged.

        Raises KeyError if *bss_name* is not registered.
        """
        ...

    def get_acl(self, bss_name: str) -> WifiAcl:
        """Return the BSS's MAC ACL state (mode + entries).

        Raises KeyError if *bss_name* is not registered.
        """
        ...
