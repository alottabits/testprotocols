"""WiFi client operations — compose wifi_client + wifi_bss templates.

Receives resolved template instances from the caller. Thin wrappers
(disconnect, is_connected, list_ssids) are deleted — step definitions call
the template method directly.
"""

from __future__ import annotations

from testprotocols.wifi_bss import WifiBss
from testprotocols.wifi_client import WifiClient


def connect_wifi_client(
    wifi_client: WifiClient,
    wifi_bss: WifiBss,
    bss_name: str,
    password: str | None = None,
    bssid: str | None = None,
) -> None:
    """Connect WiFi client using the SSID retrieved from the AP's BSS config.

    *bss_name* is the logical handle the BSS was registered under via
    ``WifiBss.create_bss``. The operation reads the broadcast SSID from
    ``wifi_bss.get_bss_config(bss_name).ssid`` and asks the client to
    associate to it.
    """
    config = wifi_bss.get_bss_config(bss_name)
    wifi_client.wifi_client_connect(config.ssid, password, bssid=bssid)


def scan_ssid(wifi_client: WifiClient, ssid_name: str) -> bool:
    """Return True if *ssid_name* is visible in the scan results."""
    return ssid_name in wifi_client.list_wifi_ssids()
