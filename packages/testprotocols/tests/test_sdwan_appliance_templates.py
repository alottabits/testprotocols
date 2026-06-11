"""Tests for the SD-WAN appliance Protocol shapes.

Covers the vendor-neutral managed-appliance capability protocols composed by
``SdwanApplianceDevice`` (distinct from the Linux digital twin's
``SdwanRouterDevice``). Each Protocol's ``expected_methods`` set is the
authoritative contract — the Protocol class must declare at least those names
in ``__protocol_attrs__`` and be ``@runtime_checkable``.
"""

from __future__ import annotations

import importlib

import pytest

PROTOCOLS = [
    (
        "L3Firewall",
        "testprotocols.l3_firewall",
        {
            "set_outbound_rules",
            "get_outbound_rules",
            "set_inbound_rules",
            "get_inbound_rules",
        },
    ),
    (
        "L7Firewall",
        "testprotocols.l7_firewall",
        {
            "set_rules",
            "get_rules",
        },
    ),
    (
        "ContentFiltering",
        "testprotocols.content_filtering",
        {
            "set_blocked_categories",
            "get_blocked_categories",
            "set_url_rules",
            "get_url_rules",
        },
    ),
    (
        "TrafficShaping",
        "testprotocols.traffic_shaping",
        {
            "set_uplink_bandwidth",
            "get_uplink_bandwidth",
            "set_global_client_bandwidth",
            "get_global_client_bandwidth",
            "set_shaping_rules",
            "get_shaping_rules",
        },
    ),
    (
        "ApplianceNat",
        "testprotocols.appliance_nat",
        {
            "set_one_to_one_rules",
            "get_one_to_one_rules",
            "set_one_to_many_rules",
            "get_one_to_many_rules",
            "set_port_forwarding_rules",
            "get_port_forwarding_rules",
        },
    ),
    (
        "ApplianceUplinks",
        "testprotocols.appliance_uplinks",
        {
            "get_uplinks",
            "get_uplink",
        },
    ),
    (
        "SyslogConfig",
        "testprotocols.syslog_config",
        {
            "set_syslog_servers",
            "get_syslog_servers",
        },
    ),
]


@pytest.mark.parametrize(("class_name", "module", "expected_methods"), PROTOCOLS)
def test_is_runtime_checkable(class_name: str, module: str, expected_methods: set[str]) -> None:
    """Each appliance Protocol must be ``@runtime_checkable``."""
    cls = getattr(importlib.import_module(module), class_name)
    assert getattr(cls, "_is_runtime_protocol", False), (
        f"{class_name} is not a @runtime_checkable Protocol"
    )


@pytest.mark.parametrize(("class_name", "module", "expected_methods"), PROTOCOLS)
def test_protocol_shape(class_name: str, module: str, expected_methods: set[str]) -> None:
    """Each appliance Protocol declares at least the expected method set."""
    cls = getattr(importlib.import_module(module), class_name)
    actual = set(cls.__protocol_attrs__)
    assert expected_methods <= actual, f"{class_name} missing: {expected_methods - actual}"
