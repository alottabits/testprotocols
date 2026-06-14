"""Protocol-shape conformance for the L2 switch capability protocols.

Each entry is the authoritative contract: the Protocol must be
``@runtime_checkable`` and declare at least ``expected_methods`` in
``__protocol_attrs__``. Mirrors ``test_sdwan_appliance_templates.py``.
"""

from __future__ import annotations

import importlib

import pytest

PROTOCOLS = [
    (
        "SwitchPorts",
        "testprotocols.switch_ports",
        {"list_ports", "get_port", "set_port"},
    ),
    ("SwitchVlans", "testprotocols.switch_vlans",
     {"list_vlans", "create_vlan", "delete_vlan"}),
    ("SpanningTree", "testprotocols.spanning_tree",
     {"set_mode", "get_mode", "set_bridge_priority",
      "set_port_config", "get_port_config", "get_port_state"}),
    ("LinkAggregation", "testprotocols.link_aggregation",
     {"list_groups", "set_group", "remove_group"}),
    ("PortPoe", "testprotocols.port_poe",
     {"set_enabled", "set_priority", "get_status"}),
    ("PortSecurity", "testprotocols.port_security",
     {"set_access_policy", "get_access_policy"}),
    ("FirstHopSecurity", "testprotocols.first_hop_security",
     {"set_dhcp_snooping", "set_dhcp_snooping_trust", "get_dhcp_bindings",
      "set_dai", "set_arp_trust"}),
    ("StormControl", "testprotocols.storm_control",
     {"set_config", "get_config"}),
    ("SwitchAcl", "testprotocols.switch_acl",
     {"set_acl", "get_acl"}),
    ("Discovery", "testprotocols.discovery", {"get_neighbors"}),
    ("MacTable", "testprotocols.mac_table", {"get_mac_table"}),
    ("PortStatus", "testprotocols.port_status",
     {"list_port_status", "get_port_status"}),
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
