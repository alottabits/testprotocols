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
from testprotocols.models.ports import PortRange
from testprotocols.models.sdwan_appliance import RuleAction, RuleProtocol


class PortMode(StrEnum):
    """Switchport framing mode.

    ``ACCESS`` and ``TRUNK`` are universal — all managed-switch drivers must support them.
    ``ROUTED`` models a routed / "no-switchport" physical port and is only meaningful on
    an L3 switch; an L2-only driver raises unsupported-capability if asked to set it.
    """

    ACCESS = "access"
    TRUNK = "trunk"
    ROUTED = "routed"  # routed / no-switchport port; L3Switch only


class PortAdminState(StrEnum):
    """Administrative enable/disable state of a port."""

    ENABLED = "enabled"
    DISABLED = "disabled"


class LinkState(StrEnum):
    """Observed per-port link state."""

    UP = "up"
    DOWN = "down"
    DISABLED = "disabled"


class Duplex(StrEnum):
    """Port duplex mode (full, half, or auto-negotiated)."""

    FULL = "full"
    HALF = "half"
    AUTO = "auto"


class AggregationMode(StrEnum):
    """Link-aggregation negotiation mode (LACP or static)."""

    LACP = "lacp"
    STATIC = "static"


class PoeStatus(StrEnum):
    """Observed Power-over-Ethernet delivery state for a port."""

    DELIVERING = "delivering"
    DISABLED = "disabled"
    FAULT = "fault"
    SEARCHING = "searching"
    OFF = "off"


class PoePriority(StrEnum):
    """PoE port priority used when total power budget is constrained."""

    CRITICAL = "critical"
    HIGH = "high"
    LOW = "low"


class AccessPolicyType(StrEnum):
    """Port-level admission-control policy (open, MAC-based, or 802.1X)."""

    OPEN = "open"
    MAC_ALLOW_LIST = "mac_allow_list"
    STICKY_MAC = "sticky_mac"
    DOT1X = "dot1x"


class AclDirection(StrEnum):
    """Direction in which a port ACL is applied."""

    INGRESS = "ingress"
    EGRESS = "egress"


class DiscoveryProtocol(StrEnum):
    """Link-layer discovery. Only the open IEEE 802.1AB standard is a member;
    a vendor's proprietary discovery normalizes onto the same LLDP-shaped read."""

    LLDP = "lldp"


class StormControlType(StrEnum):
    """Traffic category that storm-control rate limiting is applied to."""

    BROADCAST = "broadcast"
    MULTICAST = "multicast"
    UNKNOWN_UNICAST = "unknown_unicast"


class StormControlUnit(StrEnum):
    """The unit of a storm-control threshold: percent of line rate, or packets per second."""

    PERCENT = "percent"
    PPS = "pps"


class QosTrustMode(StrEnum):
    """Which QoS marking field the port trusts for inbound classification."""

    DSCP = "dscp"
    COS = "cos"
    UNTRUSTED = "untrusted"


class FhsTrustState(StrEnum):
    """First-hop-security trust level assigned to a port."""

    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"


class FhsScope(StrEnum):
    """Scope at which a first-hop-security feature (e.g. DHCP snooping) operates."""

    GLOBAL = "global"
    PER_VLAN = "per_vlan"


class BindingSource(StrEnum):
    """How a first-hop-security binding-table entry was learned."""

    DYNAMIC_SNOOPING = "dynamic_snooping"
    STATIC = "static"


@dataclass
class SwitchPort:
    """A switchport — the first-class object of a switch."""

    name: str
    mode: PortMode
    enabled: bool = True
    native_vlan: int | None = None
    allowed_vlans: list[int] = field(default_factory=list[int])
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
    allowed_macs: list[str] = field(default_factory=list[str])
    max_macs: int | None = None
    sticky: bool = False


@dataclass
class StormControlConfig:
    """Per-port storm-control thresholds, keyed by traffic type.

    *unit* is the :class:`StormControlUnit` every threshold is in; ``None`` means "as the
    driver reads it": the driver reports the product's own unit, and a writer that leaves
    it ``None`` gets the driver's default. A driver that cannot honour the requested unit
    raises ``ValueError``.
    """

    port: str
    thresholds: dict[StormControlType, float] = field(default_factory=dict[StormControlType, float])
    unit: StormControlUnit | None = None


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


@dataclass(frozen=True)
class QosClassifier:
    """What a QoS rule selects: a VLAN, a protocol and source and destination ports.

    Every field that is left out places no restriction: ``vlan`` and ``protocol``
    are ``None``, the port tuples are empty (any port). A rule selects the traffic
    that satisfies all of the fields it sets. ``vlan`` is ``1`` to ``4094``;
    ``protocol`` is a :class:`~testprotocols.models.RuleProtocol`; the ports are tuples
    of :class:`~testprotocols.models.PortRange`. A classifier of a :class:`QosRule`
    holds at most one source and one destination range, as the released text could
    spell only that.
    """

    vlan: int | None = None
    protocol: RuleProtocol | None = None
    src_ports: tuple[PortRange, ...] = ()
    dst_ports: tuple[PortRange, ...] = ()


@dataclass
class QosRule:
    """A QoS classification rule (classifier -> DSCP/CoS marking).

    The selected traffic has two forms. ``classifier`` is a :class:`QosClassifier`
    (VLAN, protocol, source and destination port), or ``None`` for every frame or for
    a selection a classifier cannot express. ``match`` is the released text form, a
    vendor-neutral classifier expression (``""`` for every frame), deprecated. The
    released contract gave the text no grammar: free text is legal. The neutral
    spelling of a classifier is a comma list of ``key=value`` terms: ``vlan``,
    ``protocol``, ``srcPort`` / ``srcPortRange`` and ``dstPort`` / ``dstPortRange`` (a
    port or an ``a-b`` range). A driver fills either field, or both; when both are
    filled they describe the same traffic. ``match`` stays required, and a driver that
    fills only ``classifier`` passes ``match=None``. ``classifier=None`` is itself a value
    ("every frame"), so a rule with both fields ``None`` is read as every frame, not as
    an unfilled pair. At removal, ``match`` goes and ``classifier`` becomes required.

    A rule also flows into a driver (``SwitchQos.set_rules``). A caller building one for
    a write member fills both forms until removal: a driver not yet updated reads only
    ``match``. A driver implementing a write member reads ``classifier`` when it is
    filled, else ``match``.

    The driver maps the selection to its product's QoS classifier; ``dscp`` and
    ``cos`` are the resulting mark values.
    """

    name: str
    match: str | None
    dscp: int | None = None
    cos: int | None = None
    classifier: QosClassifier | None = field(default=None, kw_only=True)


@dataclass
class FhsBinding:
    """A first-hop-security binding-table entry (DHCP snooping / DAI).

    Note: a driver returning static bindings MUST set ``source=BindingSource.STATIC``
    explicitly — static entries are immune to ageing and differ operationally from
    snooped ones, so do not rely on the default for static tables.
    """

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
