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
from typing import override

from testprotocols.models._sync import SyncedField, assign, settle
from testprotocols.models.l2_common import StpGuard
from testprotocols.models.ports import PortRange
from testprotocols.models.sdwan_appliance import PortMatch, RuleAction, RuleProtocol, TrafficMatch


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

    Threshold units are driver-normalized (percent of line rate or pps); the
    plugin maps the product's representation.
    """

    port: str
    thresholds: dict[StormControlType, float] = field(default_factory=dict[StormControlType, float])


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


def _port_range(text: str) -> PortRange:
    if not (text.isascii() and text.isdigit()):
        raise ValueError(f"{text!r} is not a port number")
    return PortRange.single(int(text))


def _port_span(text: str) -> PortRange:
    first, dash, last = text.partition("-")
    if not dash:
        raise ValueError(f"{text!r} is not a first-last port range")
    low, high = _port_range(first), _port_range(last)
    return PortRange(low.first, high.first)


def _parse_classifier(text: str) -> TrafficMatch | None:
    """The classifier of the released ``match`` text, ``None`` for the empty text.

    The released text is a comma list of ``key=value`` terms. The only terms a
    :data:`TrafficMatch` can express are destination ports: ``dstPort=<port>`` and
    ``dstPortRange=<first>-<last>``. Every other term (``vlan``, ``protocol``,
    ``srcPort``, ``srcPortRange``, any other key, the free form ``"vlan 10"``)
    raises ``ValueError``.
    """
    if not isinstance(text, str):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(f"QosRule.match takes text, not {text!r}")
    body = text.strip()
    if body == "":
        return None
    ranges: list[PortRange] = []
    for term in body.split(","):
        key, equals, value = term.strip().partition("=")
        try:
            if not equals or key not in ("dstPort", "dstPortRange"):
                raise ValueError(f"the term {term.strip()!r} is not a destination port")
            ranges.append(_port_range(value) if key == "dstPort" else _port_span(value))
        except ValueError as bad:
            raise ValueError(
                f"QosRule.match {text!r} cannot be expressed as a traffic classifier: {bad}; "
                "only destination ports (dstPort=<port>, dstPortRange=<first>-<last>) can be"
            ) from None
    return PortMatch(tuple(ranges))


def _format_classifier(value: TrafficMatch | None) -> str:
    if value is None:
        return ""
    if not isinstance(value, PortMatch):  # _check_classifier admits nothing else
        raise TypeError(f"QosRule.classifier takes a PortMatch or None, not {value!r}")
    return ",".join(
        f"dstPort={r.first}" if r.first == r.last else f"dstPortRange={r.first}-{r.last}"
        for r in value.ports
    )


def _check_classifier(value: TrafficMatch | None) -> TrafficMatch | None:
    if value is None or isinstance(value, PortMatch):
        return value
    if isinstance(value, TrafficMatch):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise ValueError(
            "a switch QoS classifier matches destination ports only (a PortMatch), "
            f"not {type(value).__name__}"
        )
    raise TypeError(f"QosRule.classifier takes a PortMatch or None, not {value!r}")


_QOS_PAIRS = (
    SyncedField[TrafficMatch | None](
        "match", "classifier", _parse_classifier, _format_classifier, _check_classifier, ""
    ),
)


@dataclass
class QosRule:
    """A QoS classification rule (classifier -> DSCP/CoS marking).

    ``classifier`` selects the traffic: a :class:`~testprotocols.models.PortMatch`
    (traffic to the given destination ports) or ``None`` for every frame; any other
    :data:`~testprotocols.models.TrafficMatch` raises ``ValueError``. The driver maps
    it to its product's QoS classifier; ``dscp`` and ``cos`` are the resulting
    mark values.

    ``match`` is the released spelling, a vendor-neutral classifier expression held
    as text (``""`` for every frame), deprecated. Of the released grammar, a
    comma list of ``key=value`` terms, only destination ports map to a classifier
    (``dstPort=<port>``, ``dstPortRange=<first>-<last>``); any other expression (a
    ``vlan``, ``protocol``, ``srcPort`` or ``srcPortRange`` term, another key, or
    free text such as ``"vlan 10"``) raises ``ValueError``. The two fields always
    agree. At construction the classifier fills the text; the text alone warns
    (``DeprecationWarning``) and fills the classifier; both given and disagreeing
    raise ``ValueError``. Afterwards, through ``dataclasses.replace`` and through
    assignment, the side that changed wins. A text is kept in its canonical form
    (``"dstPort=22, dstPort=80"`` reads ``"dstPort=22,dstPort=80"``), and a non-text
    ``match`` or a non-``TrafficMatch`` ``classifier`` raises ``TypeError``.
    """

    name: str
    match: str = ""
    dscp: int | None = None
    cos: int | None = None
    classifier: TrafficMatch | None = field(default=None, kw_only=True)
    _match_seen: tuple[str, ...] | None = field(
        default=None, kw_only=True, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        settle(self, _QOS_PAIRS, "_match_seen")

    @override
    def __setattr__(self, name: str, value: object) -> None:
        assign(self, name, value, _QOS_PAIRS, "_match_seen")


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
