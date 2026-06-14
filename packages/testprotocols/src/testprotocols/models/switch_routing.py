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


@dataclass
class RoutedInterface:
    """An L3 interface — SVI, routed port, or loopback.

    ``ip_address`` is the interface IP (the SVI IP for an SVI). Reuses the
    appliance DHCP vocabulary via ``InterfaceDhcp``; this record carries only the
    L3 addressing identity.
    """

    name: str
    mode: InterfaceMode
    ip_address: str
    subnet: str
    vlan_id: int | None = None


@dataclass
class InterfaceDhcpConfig:
    """Per-interface DHCP server/relay config (reuses appliance DHCP sub-models)."""

    interface: str
    mode: DhcpMode = DhcpMode.DISABLED
    lease_seconds: int = 86400
    dns_servers: list[str] = field(default_factory=list)
    options: list[DhcpOption] = field(default_factory=list)
    reservations: list[DhcpReservation] = field(default_factory=list)
    reserved_ranges: list[tuple[str, str]] = field(default_factory=list)
    relay_targets: list[str] = field(default_factory=list)


@dataclass
class OspfInterfaceSettings:
    """Per-interface OSPF participation."""

    interface: str
    area: str
    cost: int | None = None
    passive: bool = False


@dataclass
class OspfConfig:
    """Whole-config-replace OSPF configuration."""

    enabled: bool
    router_id: str
    version: OspfVersion = OspfVersion.V2
    areas: list[str] = field(default_factory=list)
    interfaces: list[OspfInterfaceSettings] = field(default_factory=list)


@dataclass
class RedundancyGroup:
    """A first-hop-redundancy group — virtual IP + role on an interface.

    Behaviour is asserted via virtual-IP + role, not raw VRRP/HSRP internals.
    """

    group_id: int
    virtual_ip: str
    role: RedundancyRole
    interface: str
