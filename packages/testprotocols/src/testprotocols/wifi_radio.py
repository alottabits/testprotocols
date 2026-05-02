"""WiFi / WifiRadio template.

Defines the abstract contract for per-radio PHY control on a WiFi-capable
device (2.4 / 5 / 6 GHz radios). Covers admin state, channel / bandwidth /
tx power / mode configuration, regulatory-domain control, and DFS-state
read.

The template is per-device with band-keyed methods (matching the
existing palco pattern in IpInterface and WifiClient). A device with
multiple radios on the same band (e.g. dual-5GHz) is not modelled in
this release; band-string keying assumes one radio per band per device.

White-box extensions (radar-event injection, raw PHY dump) live on the
``WifiRadioWhiteBox`` extension Protocol below — see LEVELS.md for the
mandatory-vs-white-box rationale.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.wifi import WifiDfsState


@runtime_checkable
class WifiRadio(Protocol):
    """Abstract contract for per-radio WiFi PHY control."""

    # --- Discovery ---

    def list_radios(self) -> list[str]:
        """Return the bands present on this device (e.g. ``["2.4GHz", "5GHz", "6GHz"]``)."""
        ...

    # --- Admin state ---

    def set_enabled(self, band: str, enabled: bool) -> None:
        """Enable or disable the radio on *band*. Disabling shuts down the PHY entirely."""
        ...

    def get_enabled(self, band: str) -> bool:
        """Return True if the radio on *band* is administratively enabled."""
        ...

    # --- Channel / bandwidth / power / mode ---

    def set_channel(self, band: str, channel: int) -> None:
        """Set the operating channel on *band* to a specific channel number.

        Auto-channel selection is not modelled in this release — pass an explicit
        channel. Raises ValueError if *channel* is not in
        ``list_supported_channels(band)``.
        """
        ...

    def get_channel(self, band: str) -> int:
        """Return the channel currently in use on *band*."""
        ...

    def list_supported_channels(self, band: str) -> list[int]:
        """Return the channels the radio can operate on under the current regulatory domain."""
        ...

    def set_bandwidth(self, band: str, bandwidth_mhz: int) -> None:
        """Set channel bandwidth on *band*: one of 20, 40, 80, 160, 320.

        Raises ValueError if the radio does not support *bandwidth_mhz*
        (e.g. 320 on a non-Wi-Fi-7 radio).
        """
        ...

    def get_bandwidth(self, band: str) -> int:
        """Return the channel bandwidth currently in use on *band* (MHz)."""
        ...

    def set_tx_power(self, band: str, power_dbm: int) -> None:
        """Set the transmit power on *band* in dBm.

        Drivers translate to vendor units (percentage / index) internally.
        Raises ValueError if *power_dbm* is outside the radio's supported range.
        """
        ...

    def get_tx_power(self, band: str) -> int:
        """Return the transmit power currently in use on *band* (dBm)."""
        ...

    def set_mode(self, band: str, mode: str) -> None:
        """Set the 802.11 PHY mode on *band*.

        Values: ``"a"``, ``"b"``, ``"g"``, ``"n"``, ``"ac"``, ``"ax"``, ``"be"``.
        Drivers may accept compound forms (``"n/ac/ax"``) at their discretion.
        Raises ValueError if the radio does not support *mode*.
        """
        ...

    def get_mode(self, band: str) -> str:
        """Return the 802.11 PHY mode currently in use on *band*."""
        ...

    # --- Regulatory domain (device-wide) ---

    def set_country(self, country_code: str) -> None:
        """Set the regulatory domain. *country_code* is ISO 3166-1 alpha-2 (``"US"``, ``"NL"``)."""
        ...

    def get_country(self) -> str:
        """Return the configured regulatory domain as an ISO 3166-1 alpha-2 country code."""
        ...

    # --- DFS ---

    def get_dfs_state(self, band: str) -> WifiDfsState:
        """Return the current DFS state of the radio on *band*.

        Includes Channel-Availability-Check status, time remaining, and
        the Non-Occupancy List of channels currently locked out by prior
        radar detection.
        """
        ...


@runtime_checkable
class WifiRadioWhiteBox(WifiRadio, Protocol):
    """White-box extension of WifiRadio for deep PHY introspection and event injection.

    Drivers backed by ``mac80211_hwsim`` (OpenWrt with the simulator radio),
    vendor PHY-test stacks, or simulated environments satisfy this extension.
    Real APs typically satisfy only the base ``WifiRadio`` Protocol; tests
    that need radar-event injection or raw PHY introspection should pin
    against ``WifiRadioWhiteBox`` and accept that they collection-skip on
    drivers that don't satisfy it (per the ``@white_box`` scenario tag rule).
    """

    def inject_radar_event(self, band: str, channel: int | None = None) -> None:
        """Inject a synthetic radar detection event on *band*.

        Test hook for DFS automation testing. *channel* defaults to the
        radio's current channel. The OpenWrt + ``mac80211_hwsim`` driver
        is the canonical implementer; drivers without hardware/simulation
        support do not satisfy ``WifiRadioWhiteBox`` at all (rather than
        raising at call time).
        """
        ...

    def get_raw_phy_dump(self) -> str:
        """Dump raw nl80211 / vendor PHY state.

        Returns the underlying driver's PHY description verbatim (e.g.
        ``iw phy`` output on Linux). Caller parses; format is driver-dependent
        and intended for diagnostics, not for steady-state contract checks.
        """
        ...
