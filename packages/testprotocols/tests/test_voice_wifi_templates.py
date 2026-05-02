"""Tests for the voice / Wi-Fi-client Protocol shapes.

Covers: SipPhone, SipServer, WifiClient.
"""

from __future__ import annotations

import importlib

import pytest

PROTOCOLS = [
    (
        "SipPhone",
        "testprotocols.sip_phone",
        {
            "phone_start",
            "phone_config",
            "phone_kill",
            "on_hook",
            "off_hook",
            "answer",
            "dial",
            "is_idle",
            "is_dialing",
            "is_incall_dialing",
            "is_ringing",
            "is_connected",
            "is_incall_connected",
            "is_onhold",
            "is_playing_dialtone",
            "is_incall_playing_dialtone",
            "is_call_ended",
            "is_code_ended",
            "is_call_waiting",
            "is_in_conference",
            "has_off_hook_warning",
            "detect_dialtone",
            "is_line_busy",
            "reply_with_code",
            "is_call_not_answered",
            "answer_waiting_call",
            "toggle_call",
            "merge_two_calls",
            "reject_waiting_call",
            "place_call_onhold",
            "place_call_offhold",
            "press_R_button",
            "hook_flash",
            "wait_for_state",
            "press_buttons",
            "has_mwi_indicator",
            "check_voicemail",
            "is_away",
            "set_presence",
            "has_pending_offline_message",
        },
    ),
    (
        "SipServer",
        "testprotocols.sip_server",
        {
            # Properties
            "name",
            "ipv4_addr",
            "ipv6_addr",
            # Lifecycle
            "start",
            "stop",
            "restart",
            "get_status",
            # User management
            "get_online_users",
            "add_user",
            "remove_endpoint",
            "allocate_number",
            # Registration
            "get_expire_timer",
            "set_expire_timer",
            # Call state
            "get_active_calls",
            "get_rtpengine_stats",
            "verify_sip_message",
            # Voicemail
            "get_voicemail_count",
            "clear_voicemail",
            # MWI
            "get_mwi_status",
            "set_mwi_status",
            # Presence
            "get_user_presence",
            "subscribe_to_user",
            "notify_presence",
            # Offline MESSAGE
            "send_offline_message",
            "get_offline_messages",
            "clear_offline_messages",
        },
    ),
    (
        "WifiClient",
        "testprotocols.wifi_client",
        {
            "reset_wifi_iface",
            "disable_wifi",
            "enable_wifi",
            "wifi_client_connect",
            "wifi_disconnect",
            "is_wlan_connected",
            "list_wifi_ssids",
            "set_wlan_scan_channel",
            "iwlist_supported_channels",
            "change_wifi_region",
            "enable_monitor_mode",
            "disable_monitor_mode",
            "is_monitor_mode_enabled",
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
