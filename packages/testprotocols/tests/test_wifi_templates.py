"""Tests for the Wi-Fi-domain Protocol shapes.

Covers: WifiRadio, WifiRadioWhiteBox, WifiBss, WifiStations, WifiRf,
WifiTransitions, WifiMesh, WifiOnboarding.

Each Protocol's expected_methods set is the authoritative contract — the
Protocol class must declare at least those names in ``__protocol_attrs__``.

Notes
-----
- ACL methods (set_acl_mode, add_acl_entry, remove_acl_entry, clear_acl,
  get_acl) belong to ``WifiBss`` (per-BSS authorization).
- ``inject_radar_event`` is on the white-box extension ``WifiRadioWhiteBox``,
  not on the base ``WifiRadio`` Protocol.
"""

from __future__ import annotations

import importlib

import pytest

PROTOCOLS = [
    (
        "WifiRadio",
        "testprotocols.wifi_radio",
        {
            # Discovery
            "list_radios",
            # Admin state
            "set_enabled",
            "get_enabled",
            # Channel / bandwidth / power / mode
            "set_channel",
            "get_channel",
            "list_supported_channels",
            "set_bandwidth",
            "get_bandwidth",
            "set_tx_power",
            "get_tx_power",
            "set_mode",
            "get_mode",
            # Regulatory domain
            "set_country",
            "get_country",
            # DFS
            "get_dfs_state",
        },
    ),
    (
        "WifiRadioWhiteBox",
        "testprotocols.wifi_radio",
        {
            # White-box additions on top of WifiRadio's full surface
            "inject_radar_event",
            "get_raw_phy_dump",
        },
    ),
    (
        "WifiBss",
        "testprotocols.wifi_bss",
        {
            # Lifecycle
            "create_bss",
            "delete_bss",
            "list_bss",
            "get_bss_config",
            # Admin state
            "set_enabled",
            # SSID broadcast
            "set_ssid",
            "set_broadcast_enabled",
            # Security
            "set_security",
            # Per-BSS MAC ACL
            "set_acl_mode",
            "add_acl_entry",
            "remove_acl_entry",
            "clear_acl",
            "get_acl",
            # VLAN binding
            "set_vlan",
            # Capacity / timing
            "set_max_clients",
            "set_dtim_period",
            # Captive portal
            "set_captive_portal",
        },
    ),
    (
        "WifiStations",
        "testprotocols.wifi_stations",
        {
            # Inspection
            "list_associated_stations",
            "get_station",
            # Admin disconnect
            "disconnect_station",
        },
    ),
    (
        "WifiRf",
        "testprotocols.wifi_rf",
        {
            # Scan
            "scan",
            "get_neighbors",
            # Channel telemetry
            "get_channel_utilization",
            "get_noise_floor",
            # Cumulative counters
            "get_radio_stats",
        },
    ),
    (
        "WifiTransitions",
        "testprotocols.wifi_transitions",
        {
            # Per-BSS enables
            "set_rrm_enabled",
            "set_btm_enabled",
            "set_ft_enabled",
            "get_transition_config",
            # Per-client triggers
            "send_btm_request",
            "send_neighbor_report_request",
            "send_deauth",
        },
    ),
    (
        "WifiMesh",
        "testprotocols.wifi_mesh",
        {
            # Admin state
            "set_enabled",
            # Status and topology
            "get_mesh_status",
            "get_topology",
            # Backhaul control
            "set_backhaul_band",
            "set_backhaul_channel",
            # Agent management
            "add_agent",
            "remove_agent",
            # DPP enrollee
            "get_dpp_uri",
            "start_dpp_enrollee",
            # WPS / PSK enrollee
            "trigger_wps_enrollee",
            "set_mesh_psk_for_enrollment",
            # Cross-mesh client steering
            "steer_client",
        },
    ),
    (
        "WifiOnboarding",
        "testprotocols.wifi_onboarding",
        {
            # WPS — per-BSS admin state
            "set_wps_enabled",
            "get_wps_enabled",
            # WPS — session triggers
            "trigger_wps_pbc",
            "trigger_wps_pin",
            "get_wps_device_pin",
            # DPP — AP as configurator
            "enroll_client_via_dpp",
        },
    ),
]


@pytest.mark.parametrize(("class_name", "module", "expected_methods"), PROTOCOLS)
def test_is_runtime_checkable(class_name: str, module: str, expected_methods: set[str]) -> None:
    cls = getattr(importlib.import_module(module), class_name)
    assert getattr(cls, "_is_runtime_protocol", False), (
        f"{class_name} is not a @runtime_checkable Protocol"
    )


@pytest.mark.parametrize(("class_name", "module", "expected_methods"), PROTOCOLS)
def test_protocol_shape(class_name: str, module: str, expected_methods: set[str]) -> None:
    cls = getattr(importlib.import_module(module), class_name)
    actual = set(cls.__protocol_attrs__)
    assert expected_methods <= actual, f"{class_name} missing: {expected_methods - actual}"


def test_acl_methods_live_on_wifi_bss_not_stations() -> None:
    """Per-BSS MAC ACL methods belong to WifiBss; WifiStations must not declare them."""
    from testprotocols.wifi_bss import WifiBss
    from testprotocols.wifi_stations import WifiStations

    acl_methods = {
        "set_acl_mode",
        "add_acl_entry",
        "remove_acl_entry",
        "clear_acl",
        "get_acl",
    }
    bss_attrs = set(WifiBss.__protocol_attrs__)
    stations_attrs = set(WifiStations.__protocol_attrs__)
    assert acl_methods <= bss_attrs, f"WifiBss missing ACL methods: {acl_methods - bss_attrs}"
    assert acl_methods.isdisjoint(stations_attrs), (
        f"WifiStations unexpectedly declares ACL methods: {acl_methods & stations_attrs}"
    )


def test_inject_radar_event_lives_on_white_box_not_base() -> None:
    """``inject_radar_event`` is white-box-only; the base WifiRadio Protocol must not declare it."""
    from testprotocols.wifi_radio import WifiRadio, WifiRadioWhiteBox

    base_attrs = set(WifiRadio.__protocol_attrs__)
    wb_attrs = set(WifiRadioWhiteBox.__protocol_attrs__)
    assert "inject_radar_event" not in base_attrs, (
        "inject_radar_event must not be on base WifiRadio Protocol"
    )
    assert "inject_radar_event" in wb_attrs, (
        "inject_radar_event must be on WifiRadioWhiteBox extension"
    )
