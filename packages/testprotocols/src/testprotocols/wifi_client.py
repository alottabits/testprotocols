"""WiFi / WifiClient template.

Defines the abstract contract for WiFi client operations including
association, scanning, and monitor-mode management.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class WifiClient(Protocol):
    """Abstract contract for WiFi client operations."""

    def reset_wifi_iface(self) -> None:
        """Reset the WiFi interface to its default state."""
        ...

    def disable_wifi(self) -> None:
        """Disable the WiFi radio."""
        ...

    def enable_wifi(self) -> None:
        """Enable the WiFi radio."""
        ...

    def wifi_client_connect(
        self,
        ssid_name: str,
        password: str | None = None,
        security_mode: str | None = None,
        bssid: str | None = None,
    ) -> None:
        """Connect to *ssid_name* using the supplied credentials and security mode."""
        ...

    def wifi_disconnect(self) -> None:
        """Disconnect from the current WiFi network."""
        ...

    def is_wlan_connected(self) -> bool:
        """Return True if the WLAN interface is currently connected."""
        ...

    def list_wifi_ssids(self) -> list[str]:
        """Return a list of visible SSIDs from a scan."""
        ...

    def set_wlan_scan_channel(self, channel: str) -> None:
        """Set the WiFi scan channel to *channel*."""
        ...

    def iwlist_supported_channels(self, wifi_band: str) -> list[str]:
        """Return the list of channels supported by the adapter for *wifi_band*."""
        ...

    def change_wifi_region(self, country: str) -> None:
        """Change the regulatory domain to *country* (ISO 3166-1 alpha-2)."""
        ...

    def enable_monitor_mode(self) -> None:
        """Enable monitor mode on the WiFi interface."""
        ...

    def disable_monitor_mode(self) -> None:
        """Disable monitor mode and return the interface to managed mode."""
        ...

    def is_monitor_mode_enabled(self) -> bool:
        """Return True if the WiFi interface is in monitor mode."""
        ...
