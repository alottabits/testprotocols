"""Tests for WAN-edge Protocol shapes.

Covers: Router, WanLinkAdmin, StaticRoutes, Bgp, SdwanPolicyManager, MulticastClient.
"""

from __future__ import annotations

import importlib

import pytest

PROTOCOLS = [
    (
        "Router",
        "testprotocols.router",
        {
            "get_active_wan_interface",
            "get_wan_interface_status",
            "get_wan_path_metrics",
            "get_link_health",
            "get_telemetry",
            "get_routing_table",
        },
    ),
    (
        "WanLinkAdmin",
        "testprotocols.wan_link_admin",
        {
            "bring_wan_down",
            "bring_wan_up",
        },
    ),
    (
        "StaticRoutes",
        "testprotocols.static_routes",
        {
            "add_static_route",
            "remove_static_route",
            "list_static_routes",
        },
    ),
    (
        "Bgp",
        "testprotocols.bgp",
        {
            "set_bgp_config",
            "get_bgp_config",
            "get_bgp_neighbors",
            "get_learned_routes",
        },
    ),
    (
        "SdwanPolicyManager",
        "testprotocols.sdwan_policy_manager",
        {
            "apply_policy",
            "remove_policy",
            "configure_sla_policy",
            "remove_sla_policy",
            "get_application_flows",
            "set_uplink_selection",
            "get_uplink_selection",
            "get_default_uplink",
            "set_default_uplink",
        },
    ),
    (
        "MulticastClient",
        "testprotocols.multicast_client",
        {"send_mldv2_report"},
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


def test_router_excludes_link_admin_methods() -> None:
    """Forced link-down moved off Router to the dedicated WanLinkAdmin
    capability (host-substrate split — an API-managed appliance cannot
    admin-down its own uplink; see SPLITS.md)."""
    from testprotocols.router import Router

    attrs = set(Router.__protocol_attrs__)
    for moved in ("bring_wan_down", "bring_wan_up"):
        assert moved not in attrs, f"{moved} should have moved off Router"


def test_sdwan_policy_manager_excludes_firewall_methods() -> None:
    """Firewall-rule administration moved off SdwanPolicyManager to the dedicated
    l3_firewall / l7_firewall capabilities (coherent-domain split — see SPLITS.md)."""
    from testprotocols.sdwan_policy_manager import SdwanPolicyManager

    attrs = set(SdwanPolicyManager.__protocol_attrs__)
    for moved in ("apply_firewall_rule", "remove_firewall_rule", "get_firewall_rules"):
        assert moved not in attrs, f"{moved} should have moved off SdwanPolicyManager"
