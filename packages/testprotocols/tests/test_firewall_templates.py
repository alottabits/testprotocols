"""Tests for the firewall-domain Protocol shapes.

Covers: PacketFilter, Firewall, Nat, Conntrack, FirewallZones.

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
        "Firewall",
        "testprotocols.firewall",
        {
            # Inherited rule-lifecycle from PacketFilter
            "add_rule",
            "remove_rule",
            "list_rules",
            "get_rule",
            "flush_chain",
            "set_default_policy",
            "get_default_policy",
            "get_rule_counters",
            # Port-forwarding additions
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


def test_firewall_extends_packet_filter() -> None:
    """Firewall MUST be a Protocol subclass of PacketFilter (tier relationship)."""
    from testprotocols.firewall import Firewall
    from testprotocols.packet_filter import PacketFilter

    assert PacketFilter in Firewall.__mro__, (
        "Firewall must extend PacketFilter via Protocol inheritance"
    )


def test_firewall_whitebox_extends_firewall() -> None:
    """FirewallWhiteBox MUST be a Protocol subclass of Firewall."""
    from testprotocols.firewall import Firewall, FirewallWhiteBox

    assert Firewall in FirewallWhiteBox.__mro__, (
        "FirewallWhiteBox must extend Firewall via Protocol inheritance"
    )


def test_firewall_whitebox_shape() -> None:
    """FirewallWhiteBox declares the kernel-dump method set."""
    from testprotocols.firewall import FirewallWhiteBox

    expected = {"get_kernel_iptables_dump", "get_nftables_ruleset"}
    actual = set(FirewallWhiteBox.__protocol_attrs__)
    assert expected <= actual, f"FirewallWhiteBox missing: {expected - actual}"
