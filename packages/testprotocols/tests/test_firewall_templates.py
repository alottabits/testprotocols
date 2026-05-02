"""Tests for the firewall-domain Protocol shapes.

Covers: PacketFilter, Nat, PortForwarding, Conntrack, FirewallZones.

Each Protocol's ``expected_methods`` set is the authoritative contract — the
Protocol class must declare at least those names in ``__protocol_attrs__``.
"""

from __future__ import annotations

import importlib

import pytest

PROTOCOLS = [
    (
        "PacketFilter",
        "testprotocols.packet_filter",
        {
            "add_rule",
            "remove_rule",
            "list_rules",
            "get_rule",
            "flush_chain",
            "set_default_policy",
            "get_default_policy",
            "get_rule_counters",
        },
    ),
    (
        "Nat",
        "testprotocols.nat",
        {
            "add_nat_rule",
            "remove_nat_rule",
            "list_nat_rules",
            "get_nat_rule",
            "set_nat_rule_enabled",
            "flush_nat_rules",
            "get_nat_rule_counters",
        },
    ),
    (
        "PortForwarding",
        "testprotocols.port_forwarding",
        {
            "add_port_mapping",
            "remove_port_mapping",
            "list_port_mappings",
            "get_port_mapping",
            "set_port_mapping_enabled",
            "set_dmz_host",
            "get_dmz_host",
        },
    ),
    (
        "Conntrack",
        "testprotocols.conntrack",
        {
            "get_stats",
            "list_connections",
            "count_connections",
            "get_connection",
            "drop_connection",
            "flush_connections",
            "set_max_connections",
            "get_max_connections",
        },
    ),
    (
        "FirewallZones",
        "testprotocols.firewall_zones",
        {
            "create_zone",
            "delete_zone",
            "list_zones",
            "get_zone",
            "add_zone_interface",
            "remove_zone_interface",
            "add_zone_network",
            "remove_zone_network",
            "set_zone_defaults",
            "set_forwarding",
            "list_forwarding",
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
