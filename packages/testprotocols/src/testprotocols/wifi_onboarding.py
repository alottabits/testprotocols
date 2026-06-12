"""WiFi / WifiOnboarding template.

Defines the abstract contract for WPS and DPP (EasyConnect) client
onboarding on a WiFi-capable device: per-BSS WPS enable, PBC / PIN
trigger, device-PIN read, and DPP-based client enrollment.

Vendor uniformity is low-medium: residential / RDK-B / prpl / OpenWrt
stacks expose all of these as first-class operations; enterprise stacks
commonly disable WPS entirely and offer DPP only sporadically. Drivers
without support for a specific onboarding method raise
NotImplementedError.

Mesh agent onboarding (M1/M2 / DPP between APs) lives on WifiMesh;
this template is exclusively for STA-side (client) onboarding.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class WifiOnboarding(Protocol):
    """Abstract contract for WPS and DPP client onboarding."""

    # --- WPS — per-BSS admin state ---

    def set_wps_enabled(self, bss_name: str, enabled: bool) -> None:
        """Enable or disable WPS support on *bss_name*.

        Raises KeyError if *bss_name* is not registered.
        """
        ...

    def get_wps_enabled(self, bss_name: str) -> bool:
        """Return True if WPS is currently enabled on *bss_name*.

        Raises KeyError if *bss_name* is not registered.
        """
        ...

    # --- WPS — session triggers ---

    def trigger_wps_pbc(self, bss_name: str, window_seconds: float = 120.0) -> None:
        """Open a WPS Push-Button Configuration window on *bss_name*.

        Returns immediately after the window opens. The AP accepts WPS-PBC
        joins for *window_seconds* (standard WPS window is 120s); after
        that, the window closes whether or not a client joined. Tests
        verify joins by polling ``WifiStations.list_associated_stations``.

        Raises KeyError if *bss_name* is not registered.
        Raises RuntimeError if WPS is currently disabled on *bss_name*.
        """
        ...

    def trigger_wps_pin(self, bss_name: str, pin: str, window_seconds: float = 120.0) -> None:
        """Open a WPS PIN-mode window on *bss_name* expecting *pin*.

        Returns immediately. The AP accepts a WPS-PIN join from any client
        presenting *pin* for *window_seconds*. *pin* is 4 or 8 digits per
        WPS spec; drivers raise ValueError on malformed PINs.

        Raises KeyError if *bss_name* is not registered.
        Raises RuntimeError if WPS is currently disabled on *bss_name*.
        """
        ...

    def get_wps_device_pin(self, bss_name: str) -> str:
        """Return the AP's own WPS device PIN for *bss_name*.

        The device PIN is the 8-digit PIN burned into the AP that a client
        can use to enroll without an explicitly-set PIN session. Useful in
        tests where the client drives WPS-PIN onboarding and needs to know
        the AP's PIN.

        Raises KeyError if *bss_name* is not registered.
        """
        ...

    # --- DPP / EasyConnect — AP as configurator ---

    def enroll_client_via_dpp(
        self,
        client_dpp_uri: str,
        bss_name: str,
        timeout: float = 60.0,
    ) -> None:
        """Provision a new client onto *bss_name* via DPP, acting as configurator.

        *client_dpp_uri* is the client's DPP bootstrap URI (typically scanned
        from the client's QR code or obtained via NFC / out-of-band channel).
        The AP performs the DPP authentication and configuration exchange,
        delivering the SSID + credentials for *bss_name* to the client.

        Blocks until the DPP exchange completes (driver has confirmed
        configuration delivery to the client) or *timeout* seconds elapse.
        The client's subsequent association is asynchronous — tests verify
        via ``WifiStations.list_associated_stations``.

        Raises KeyError if *bss_name* is not registered.
        Raises ValueError if *client_dpp_uri* is malformed.
        Raises TimeoutError if the DPP exchange does not complete within *timeout*.
        """
        ...
