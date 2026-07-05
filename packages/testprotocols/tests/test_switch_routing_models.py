"""Tests for the L3 switch routing models."""

from __future__ import annotations


def test_route_origin_and_backcompat() -> None:
    from testprotocols.models.wan_edge import RouteEntry, RouteOrigin

    assert RouteOrigin.OSPF == "ospf"
    # back-compat: the existing 4-arg constructor still works, origin defaults
    e = RouteEntry(destination="10.0.0.0/24", gateway="10.0.0.1", interface="vlan10", metric=1)
    assert e.origin == RouteOrigin.UNKNOWN
    # and origin can be set explicitly
    e2 = RouteEntry(
        destination="0.0.0.0/0", gateway="1.1.1.1", interface="vlan1",
        metric=1, origin=RouteOrigin.STATIC,
    )
    assert e2.origin == "static"


def test_switch_routing_enums() -> None:
    from testprotocols.models.switch_routing import (
        InterfaceMode,
        OspfVersion,
        RedundancyRole,
        RouteOrigin,  # re-exported for convenience
    )

    assert InterfaceMode.SVI == "svi"
    assert OspfVersion.V2 == "v2"
    assert RedundancyRole.PRIMARY == "primary"
    assert RouteOrigin.BGP == "bgp"


def test_switch_routing_records() -> None:
    from testprotocols.models.switch_routing import (
        InterfaceDhcpConfig,
        InterfaceMode,
        OspfConfig,
        OspfInterfaceSettings,
        RedundancyGroup,
        RedundancyRole,
        RoutedInterface,
    )

    ri = RoutedInterface(
        name="vlan10",
        mode=InterfaceMode.SVI,
        ip_address="10.0.10.1",
        subnet="10.0.10.0/24",
        vlan_id=10,
    )
    assert ri.vlan_id == 10
    d = InterfaceDhcpConfig(interface="vlan10")
    assert d.mode == "disabled" and d.relay_targets == []
    o = OspfConfig(enabled=True, router_id="1.1.1.1")
    assert o.version == "v2" and o.interfaces == []
    oi = OspfInterfaceSettings(interface="vlan10", area="0.0.0.0")
    assert oi.passive is False
    g = RedundancyGroup(
        group_id=1, virtual_ip="10.0.10.254", role=RedundancyRole.PRIMARY, interface="vlan10"
    )
    assert g.virtual_ip == "10.0.10.254"
