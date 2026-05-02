"""Tests for testoperations.wifi_client module."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from testoperations.wifi_client import (
    connect_wifi_client,
    scan_ssid,
)

# ---------------------------------------------------------------------------
# connect_wifi_client
# ---------------------------------------------------------------------------


class TestConnectWifiClient:
    def test_fetches_ssid_from_bss_config_and_connects(self):
        wifi = MagicMock()
        bss = MagicMock()
        bss.get_bss_config.return_value = SimpleNamespace(ssid="AutoSSID")

        connect_wifi_client(wifi, bss, bss_name="home", password="pass")

        bss.get_bss_config.assert_called_once_with("home")
        wifi.wifi_client_connect.assert_called_once_with("AutoSSID", "pass", bssid=None)

    def test_passes_bssid(self):
        wifi = MagicMock()
        bss = MagicMock()
        bss.get_bss_config.return_value = SimpleNamespace(ssid="Net")

        connect_wifi_client(wifi, bss, bss_name="guest", bssid="aa:bb:cc:dd:ee:ff")

        wifi.wifi_client_connect.assert_called_once_with("Net", None, bssid="aa:bb:cc:dd:ee:ff")


# ---------------------------------------------------------------------------
# scan_ssid
# ---------------------------------------------------------------------------


class TestScanSsid:
    def test_returns_true_when_ssid_found(self):
        wifi = MagicMock()
        wifi.list_wifi_ssids.return_value = ["HomeNetwork", "GuestNetwork"]
        assert scan_ssid(wifi, "HomeNetwork") is True

    def test_returns_false_when_ssid_not_found(self):
        wifi = MagicMock()
        wifi.list_wifi_ssids.return_value = ["HomeNetwork"]
        assert scan_ssid(wifi, "GuestNetwork") is False

    def test_calls_list_wifi_ssids(self):
        wifi = MagicMock()
        wifi.list_wifi_ssids.return_value = []
        scan_ssid(wifi, "AnySSID")
        wifi.list_wifi_ssids.assert_called_once_with()
