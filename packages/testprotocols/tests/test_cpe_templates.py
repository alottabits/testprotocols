"""Tests for TR-069 / CPE-management Protocol shapes.

Covers: Tr069Client, Tr069Server, Tr069Gui, DeviceManagement,
DeviceLifecycle, HwConsole.
"""

from __future__ import annotations

import importlib

import pytest

PROTOCOLS = [
    (
        "Tr069Client",
        "testprotocols.tr069_client",
        {"is_tr069_connected", "get_tr069_log"},
    ),
    (
        "Tr069Server",
        "testprotocols.tr069_server",
        {
            "GPV",
            "SPV",
            "GPA",
            "SPA",
            "FactoryReset",
            "Reboot",
            "AddObject",
            "DelObject",
            "GPN",
            "ScheduleInform",
            "GetRPCMethods",
            "Download",
            "provision_cpe_via_tr069",
        },
    ),
    (
        "Tr069Gui",
        "testprotocols.tr069_gui",
        {
            "login",
            "logout",
            "is_logged_in",
            "search_device",
            "get_device_count",
            "filter_devices",
            "get_device_status",
            "verify_device_online",
            "get_last_inform_time",
            "reboot_device_via_gui",
            "factory_reset_via_gui",
            "delete_device_via_gui",
            "get_device_parameter_via_gui",
            "set_device_parameter_via_gui",
            "trigger_firmware_upgrade_via_gui",
            "verify_firmware_version_via_gui",
        },
    ),
    (
        "DeviceManagement",
        "testprotocols.device_management",
        {
            "get_seconds_uptime",
            "is_online",
            "get_load_avg",
            "get_memory_utilization",
            "get_running_processes",
            "get_board_logs",
            "read_event_logs",
            "get_boottime_log",
            "get_file_content",
        },
    ),
    (
        "DeviceLifecycle",
        "testprotocols.device_lifecycle",
        {
            "verify_cpe_is_booting",
            "wait_for_boot",
            "factory_reset",
            "reset",
            "finalize_boot",
        },
    ),
    (
        "HwConsole",
        "testprotocols.hw_console",
        {
            "connect_to_consoles",
            "disconnect_from_consoles",
            "get_console",
            "get_interactive_consoles",
            "power_cycle",
            "wait_for_hw_boot",
            "flash_via_bootloader",
        },
    ),
]


@pytest.mark.parametrize(("class_name", "module", "expected_methods"), PROTOCOLS)
def test_is_runtime_checkable(class_name: str, module: str, expected_methods: set[str]) -> None:
    """Each Protocol must be ``@runtime_checkable``."""
    cls = getattr(importlib.import_module(module), class_name)
    assert getattr(cls, "_is_runtime_protocol", False), (
        f"{class_name} is not a @runtime_checkable Protocol"
    )


@pytest.mark.parametrize(("class_name", "module", "expected_methods"), PROTOCOLS)
def test_protocol_shape(class_name: str, module: str, expected_methods: set[str]) -> None:
    """Each Protocol declares at least the expected method set."""
    cls = getattr(importlib.import_module(module), class_name)
    actual = set(cls.__protocol_attrs__)
    assert expected_methods <= actual, f"{class_name} missing: {expected_methods - actual}"
