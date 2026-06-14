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
