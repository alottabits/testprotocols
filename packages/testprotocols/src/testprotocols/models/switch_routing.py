"""Data models for the vendor-neutral L3 (distribution) switch capabilities.

Composed by ``devices.switch.L3Switch`` (a strict superset of ``L2Switch``).
Reuses ``DhcpMode`` / ``DhcpOption`` / ``DhcpReservation`` / ``DhcpLease`` from
``models/sdwan_appliance.py`` and ``RouteEntry`` / ``RouteOrigin`` from
``models/wan_edge.py``. Scope is the **default VRF** — multi-VRF is deferred
(GAPS.md). Vendor neutrality is part of the contract: no product name, vendor id,
or ``native`` bucket appears here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from testprotocols.models.sdwan_appliance import (
    DhcpMode,
    DhcpOption,
    DhcpReservation,
)
from testprotocols.models.wan_edge import RouteOrigin  # re-export

__all__ = [
    "DhcpMode",
    "InterfaceDhcpConfig",
    "InterfaceMode",
    "OspfConfig",
    "OspfInterfaceSettings",
    "OspfVersion",
    "RedundancyGroup",
    "RedundancyRole",
    "RouteOrigin",
    "RoutedInterface",
]


class InterfaceMode(StrEnum):
    """L3 interface kind."""

    SVI = "svi"
    ROUTED = "routed"
    LOOPBACK = "loopback"


class OspfVersion(StrEnum):
    """Seeded standardized OSPF versions. ``OspfNetworkType`` / ``OspfAreaType``
    grow on evidence (open taxonomy)."""

    V2 = "v2"
    V3 = "v3"


class RedundancyRole(StrEnum):
    """First-hop-redundancy role. ``ACTIVE_ACTIVE`` is a recorded candidate
    (all-active gateways) — added on a driving test, not seeded."""

    PRIMARY = "primary"
    SPARE = "spare"
