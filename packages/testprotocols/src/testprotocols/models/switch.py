"""Data models for the vendor-neutral L2 (access) switch capabilities.

Field value-vocabularies are normalized ``StrEnum`` types owned here; records are
plain ``@dataclass``es composing them. Shared STP/FDB vocab lives in
``models/l2_common.py``; rule action/protocol enums are reused from
``models/sdwan_appliance.py``. Vendor neutrality is part of the contract — no
product name, vendor id, or ``native`` bucket appears in this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from testprotocols.models.l2_common import StpGuard
from testprotocols.models.sdwan_appliance import RuleAction, RuleProtocol


class PortMode(StrEnum):
    ACCESS = "access"
    TRUNK = "trunk"
    ROUTED = "routed"  # used only at L3 (L3Switch); access/trunk are universal


class PortAdminState(StrEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class LinkState(StrEnum):
    UP = "up"
    DOWN = "down"
    DISABLED = "disabled"


class Duplex(StrEnum):
    FULL = "full"
    HALF = "half"
    AUTO = "auto"


class AggregationMode(StrEnum):
    LACP = "lacp"
    STATIC = "static"


class PoeStatus(StrEnum):
    DELIVERING = "delivering"
    DISABLED = "disabled"
    FAULT = "fault"
    SEARCHING = "searching"
    OFF = "off"


class PoePriority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    LOW = "low"


class AccessPolicyType(StrEnum):
    OPEN = "open"
    MAC_ALLOW_LIST = "mac_allow_list"
    STICKY_MAC = "sticky_mac"
    DOT1X = "dot1x"


class AclDirection(StrEnum):
    INGRESS = "ingress"
    EGRESS = "egress"


class DiscoveryProtocol(StrEnum):
    """Link-layer discovery. Only the open IEEE 802.1AB standard is a member;
    a vendor's proprietary discovery normalizes onto the same LLDP-shaped read."""

    LLDP = "lldp"


class StormControlType(StrEnum):
    BROADCAST = "broadcast"
    MULTICAST = "multicast"
    UNKNOWN_UNICAST = "unknown_unicast"


class QosTrustMode(StrEnum):
    DSCP = "dscp"
    COS = "cos"
    UNTRUSTED = "untrusted"


class FhsTrustState(StrEnum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"


class FhsScope(StrEnum):
    GLOBAL = "global"
    PER_VLAN = "per_vlan"


class BindingSource(StrEnum):
    DYNAMIC_SNOOPING = "dynamic_snooping"
    STATIC = "static"


@dataclass
class SwitchPort:
    """A switchport — the first-class object of a switch."""

    name: str
    mode: PortMode
    enabled: bool = True
    native_vlan: int | None = None
    allowed_vlans: list[int] = field(default_factory=list)
    description: str = ""
    voice_vlan: int | None = None
    isolated: bool = False


@dataclass
class VlanDef:
    """A VLAN id/name registry entry."""

    vlan_id: int
    name: str = ""


@dataclass
class StpPortConfig:
    """Per-port spanning-tree configuration."""

    port: str
    guard: StpGuard = StpGuard.NONE
    edge: bool = False
    path_cost: int | None = None
    priority: int | None = None


@dataclass
class LinkAggregationGroup:
    """A link-aggregation group (LAG) by member ports + mode."""

    name: str
    member_ports: list[str]
    mode: AggregationMode = AggregationMode.LACP


@dataclass
class PoePortStatus:
    """Observed PoE state for a port."""

    port: str
    status: PoeStatus
    draw_watts: float | None = None
    priority: PoePriority | None = None


@dataclass
class AccessPolicy:
    """Per-port access policy (802.1X / MAB / MAC limits)."""

    port: str
    policy_type: AccessPolicyType
    allowed_macs: list[str] = field(default_factory=list)
    max_macs: int | None = None
    sticky: bool = False


@dataclass
class StormControlConfig:
    """Per-port storm-control thresholds, keyed by traffic type.

    Threshold units are driver-normalized (percent of line rate or pps); the
    plugin maps the product's representation.
    """

    port: str
    thresholds: dict[StormControlType, float] = field(default_factory=dict)


@dataclass
class SwitchAclRule:
    """One ordered switch ACL rule — unified L2 + L3/L4 match.

    Reuses ``RuleAction`` / ``RuleProtocol``; the L2 fields (``src_mac`` /
    ``dst_mac`` / ``vlan``) and the IP 5-tuple are all optional, so the same
    record serves both the L2 archetype and the L3 superset.
    """

    action: RuleAction
    protocol: RuleProtocol = RuleProtocol.ANY
    src_mac: str | None = None
    dst_mac: str | None = None
    vlan: int | None = None
    src_cidr: str = "any"
    dst_cidr: str = "any"
    src_port: str = "any"
    dst_port: str = "any"
    comment: str = ""


@dataclass
class LldpNeighbor:
    """A discovered link-layer neighbour (read-only)."""

    local_port: str
    remote_system: str
    remote_port: str
    protocol: DiscoveryProtocol = DiscoveryProtocol.LLDP
    mgmt_address: str | None = None


@dataclass
class PortStatusEntry:
    """Observed per-port link state and counters (read-only)."""

    name: str
    link_state: LinkState
    speed_mbps: int | None = None
    duplex: Duplex = Duplex.AUTO
    rx_errors: int = 0
    tx_errors: int = 0
    rx_discards: int = 0
    tx_discards: int = 0


@dataclass
class QosRule:
    """A QoS classification rule (match -> DSCP/CoS marking)."""

    name: str
    match: str
    dscp: int | None = None
    cos: int | None = None


@dataclass
class FhsBinding:
    """A first-hop-security binding-table entry (DHCP snooping / DAI)."""

    mac: str
    ip: str
    vlan: int
    port: str
    source: BindingSource = BindingSource.DYNAMIC_SNOOPING


@dataclass
class NtpServer:
    """An NTP server destination."""

    host: str
    prefer: bool = False
