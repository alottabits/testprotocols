"""Tests for the traffic-domain Protocol shapes.

Covers: IperfClient, IperfServer, IperfGenerator, NetemController, QoeBrowser.
"""

from __future__ import annotations

import importlib

import pytest

PROTOCOLS = [
    (
        "IperfClient",
        "testprotocols.iperf_client",
        {"start_traffic_sender", "stop_traffic", "get_iperf_logs"},
    ),
    (
        "IperfServer",
        "testprotocols.iperf_server",
        {"start_traffic_receiver", "stop_traffic", "get_iperf_logs"},
    ),
    (
        "IperfGenerator",
        "testprotocols.iperf_generator",
        {
            "server_ip",
            "active_flows",
            "start_traffic",
            "stop_traffic",
            "stop_all_traffic",
            "run_traffic",
        },
    ),
    (
        "NetemController",
        "testprotocols.netem_controller",
        {
            "set_impairment_profile",
            "set_interface_profile",
            "get_interface_profile",
            "get_interface_profiles",
            "clear",
            "inject_transient",
        },
    ),
    (
        "QoeBrowser",
        "testprotocols.qoe_browser",
        {
            "measure",
            "measure_productivity",
            "measure_streaming",
            "measure_conferencing",
            "attempt_outbound_connection",
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
