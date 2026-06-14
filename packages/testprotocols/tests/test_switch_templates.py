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
