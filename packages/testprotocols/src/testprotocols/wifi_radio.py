"""WiFi / WifiRadio template.

Defines the abstract contract for per-radio PHY control on a WiFi-capable
device (2.4 / 5 / 6 GHz radios). Covers admin state, channel / bandwidth /
tx power / mode configuration, regulatory-domain control, and DFS-state
read.

The template is per-device with band-keyed methods (matching the
existing vitro pattern in IpInterface and WifiClient). A device with
multiple radios on the same band (e.g. dual-5GHz) is not modelled in
this release; band-string keying assumes one radio per band per device.

White-box extensions (radar-event injection, raw PHY dump) live on the
``WifiRadioWhiteBox`` extension Protocol below — see LEVELS.md for the
mandatory-vs-white-box rationale.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols._compat import deprecated
from testprotocols.models.wifi import (
    ChannelWidth,
    WifiBand,
    WifiDfsState,
    WifiPhyMode,
)


@runtime_checkable
class WifiRadio(Protocol):
    """Abstract contract for per-radio WiFi PHY control."""

    # --- Discovery ---

    def list_radios(self) -> list[str]:
        """Return the bands present on this device (e.g. ``["2.4GHz", "5GHz", "6GHz"]``).

        Every *band* parameter of this Protocol is a
        :class:`~testprotocols.models.wifi.WifiBand`; a plain ``str`` naming one
        (``"5GHz"``) is deprecated, except for ``get_modes``, which takes the
        bare enum; any other string raises ``ValueError``.

        Announced, not yet changed: the return narrows to ``list[WifiBand]`` in a
        later release (each element is a ``str`` equal to its ``WifiBand`` today).
        """
        ...

    # --- Admin state ---

    def set_enabled(self, band: WifiBand | str, enabled: bool) -> None:
        """Enable or disable the radio on *band*. Disabling shuts down the PHY entirely."""
        ...

    def get_enabled(self, band: WifiBand | str) -> bool:
        """Return True if the radio on *band* is administratively enabled."""
        ...

    # --- Channel / bandwidth / power / mode ---

    def set_channel(self, band: WifiBand | str, channel: int) -> None:
        """Set the operating channel on *band* to a specific channel number.

        Auto-channel selection is not modelled in this release — pass an explicit
        channel. Raises ValueError if *channel* is not in
        ``list_supported_channels(band)``.
        """
        ...

    def get_channel(self, band: WifiBand | str) -> int:
        """Return the channel currently in use on *band*."""
        ...

    def list_supported_channels(self, band: WifiBand | str) -> list[int]:
        """Return the channels the radio can operate on under the current regulatory domain."""
        ...

    def set_bandwidth(self, band: WifiBand | str, bandwidth_mhz: ChannelWidth | int) -> None:
        """Set channel bandwidth on *band*: a :class:`~testprotocols.models.wifi.ChannelWidth`
        (20, 40, 80, 160 or 320 MHz).

        A plain ``int`` naming a member is that member (a ``ChannelWidth`` is an ``int``);
        a number that is no member raises ``ValueError``.

        Raises ValueError if the radio does not support *bandwidth_mhz*
        (e.g. 320 on a non-Wi-Fi-7 radio).
        """
        ...

    def get_bandwidth(self, band: WifiBand | str) -> int:
        """Return the channel bandwidth currently in use on *band* (MHz).

        Announced, not yet changed: the return narrows to ``ChannelWidth`` in a
        later release (a ``ChannelWidth`` is an ``int``, so comparisons keep working).
        """
        ...

    def set_tx_power(self, band: WifiBand | str, power_dbm: int) -> None:
        """Set the transmit power on *band* in dBm.

        Drivers translate to vendor units (percentage / index) internally.
        Raises ValueError if *power_dbm* is outside the radio's supported range.
        """
        ...

    def get_tx_power(self, band: WifiBand | str) -> int:
        """Return the transmit power currently in use on *band* (dBm)."""
        ...

    def set_mode(self, band: WifiBand | str, mode: WifiPhyMode | str) -> None:
        """Set the 802.11 PHY mode on *band*.

        *mode* is a :class:`~testprotocols.models.wifi.WifiPhyMode` (``"a"``, ``"b"``,
        ``"g"``, ``"n"``, ``"ac"``, ``"ax"``, ``"be"``); a plain ``str`` naming one is
        deprecated. Drivers may accept compound forms (``"n/ac/ax"``) at their
        discretion: such a string names no member, so a driver that accepts it
        handles that ``str`` itself.
        Raises ValueError if the radio does not support *mode*.

        The radio may then operate further modes as well, which :meth:`get_modes` reports.
        """
        ...

    @deprecated(
        "Deprecated: use get_modes. Removal not before the first release 6 months after "
        "the release that deprecates it.",
        category=None,
    )
    def get_mode(self, band: WifiBand | str) -> str:
        """Return the 802.11 PHY mode currently in use on *band*.

        A radio operates a set of modes at once (TR-181
        ``Device.WiFi.Radio.{i}.OperatingStandards`` is a list), so one word cannot
        report them; a driver may return a compound form (``"n/ac/ax"``).

        Deprecated: use :meth:`get_modes`. Removal not before the first release 6 months
        after the release that deprecates it.
        """
        ...

    def get_modes(self, band: WifiBand) -> frozenset[WifiPhyMode]:
        """Return the set of 802.11 PHY modes the radio on *band* currently operates.

        *band* is a :class:`~testprotocols.models.wifi.WifiBand`: the member is new and has no
        released text form, so a caller holding the band as text converts it with
        ``WifiBand(text)``.

        A radio runs several modes at once (TR-181
        ``Device.WiFi.Radio.{i}.OperatingStandards`` is a list): a 5 GHz radio
        commonly operates ``A``, ``N``, ``AC`` and ``AX``.
        """
        ...

    # --- Regulatory domain (device-wide) ---

    def set_country(self, country_code: str) -> None:
        """Set the regulatory domain. *country_code* is ISO 3166-1 alpha-2 (``"US"``, ``"NL"``)."""
        ...

    def get_country(self) -> str:
        """Return the configured regulatory domain as an ISO 3166-1 alpha-2 country code."""
        ...

    # --- DFS ---

    def get_dfs_state(self, band: WifiBand | str) -> WifiDfsState:
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

    def inject_radar_event(self, band: WifiBand | str, channel: int | None = None) -> None:
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
