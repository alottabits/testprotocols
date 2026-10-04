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
from typing import cast, override

from testprotocols.deprecation import MODEL_FRAMES, coerce_enum
from testprotocols.models._sync import SyncedField, assign, settle
from testprotocols.models.l2_common import StpGuard
from testprotocols.models.ports import PortRange, port_tuple
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


_MAX_VLAN = 4094


@dataclass(frozen=True)
class QosClassifier:
    """What a QoS rule selects: a VLAN, a protocol and source and destination ports.

    Every field that is left out places no restriction: ``vlan`` and ``protocol``
    are ``None``, the port tuples are empty (any port). A rule selects the traffic
    that satisfies all of the fields it sets. ``vlan`` is ``1`` to ``4094`` (a bool
    or non-int raises ``TypeError``, another number ``ValueError``); ``protocol``
    is a :class:`~testprotocols.models.RuleProtocol` (a plain string naming one
    warns and converts); the ports are tuples of
    :class:`~testprotocols.models.PortRange`.
    """

    vlan: int | None = None
    protocol: RuleProtocol | None = None
    src_ports: tuple[PortRange, ...] = ()
    dst_ports: tuple[PortRange, ...] = ()

    def __post_init__(self) -> None:
        vlan: object = self.vlan
        if vlan is not None:
            if type(vlan) is not int:
                raise TypeError(f"QosClassifier.vlan must be an int, not {vlan!r}")
            if not 1 <= vlan <= _MAX_VLAN:
                raise ValueError(f"QosClassifier.vlan {vlan} is outside 1-{_MAX_VLAN}")
        if self.protocol is not None:
            object.__setattr__(
                self,
                "protocol",
                coerce_enum(
                    RuleProtocol,
                    cast("RuleProtocol | str", self.protocol),
                    what="QosClassifier.protocol",
                    skip_file_prefixes=MODEL_FRAMES,
                ),
            )
        object.__setattr__(self, "src_ports", port_tuple(self.src_ports))
        object.__setattr__(self, "dst_ports", port_tuple(self.dst_ports))


# The text the released drivers read and write: a comma list of key=value terms. These are
# the released spellings, accepted as given; the record above carries the neutral names.
_KEYS = ("vlan", "protocol", "srcPort", "srcPortRange", "dstPort", "dstPortRange")


def _port_term(value: str) -> PortRange:
    first, dash, last = value.partition("-")
    for part in (first, last) if dash else (first,):
        if not (part.isascii() and part.isdigit()):
            raise ValueError(f"{value!r} is not a port or port range")
    return PortRange(int(first), int(last) if dash else int(first))


def _vlan_term(value: str) -> int:
    if not (value.isascii() and value.isdigit()):
        raise ValueError(f"{value!r} is not a VLAN id")
    return int(value)


def _parse_classifier(text: str) -> QosClassifier | None:
    """The classifier the released ``match`` text spells, or ``None``.

    The released contract gave the text no grammar. Text that is a comma list of
    ``key=value`` terms over the keys the released producers write (a VLAN, a
    protocol, source and destination ports, a port or an ``a-b`` range) gives a
    classifier. Anything else (free text such as ``"vlan 10"``, another key, a value
    that is not a VLAN, protocol or port) has no classifier: ``None``, with the text
    kept as given. The empty text is ``None`` as well (every frame). A repeated
    key, or both the port and the range key of one direction, raises ``ValueError``.
    """
    if not isinstance(text, str):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(f"QosRule.match takes text, not {text!r}")
    body = text.strip()
    if body == "":
        return None
    seen: dict[str, str] = {}
    terms: list[tuple[str, str]] = []
    for term in body.split(","):
        key, equals, value = term.strip().partition("=")
        if not equals or key not in _KEYS:
            return None
        terms.append((key, value.strip()))
    for key, value in terms:
        group = key.removesuffix("Range")
        if group in seen:
            raise ValueError(f"QosRule.match {text!r}: the term {group!r} is given twice")
        seen[group] = value
    try:
        vlan = _vlan_term(seen["vlan"]) if "vlan" in seen else None
        protocol = RuleProtocol(seen["protocol"].lower()) if "protocol" in seen else None
        src = (_port_term(seen["srcPort"]),) if "srcPort" in seen else ()
        dst = (_port_term(seen["dstPort"]),) if "dstPort" in seen else ()
        return QosClassifier(vlan=vlan, protocol=protocol, src_ports=src, dst_ports=dst)
    except ValueError:
        return None


def _port_text(key: str, ranges: tuple[PortRange, ...]) -> list[str]:
    if not ranges:
        return []
    (only,) = ranges
    if only.first == only.last:
        return [f"{key}={only.first}"]
    return [f"{key}Range={only.first}-{only.last}"]


def _format_classifier(value: QosClassifier | None) -> str:
    if value is None:
        return ""
    terms: list[str] = []
    if value.vlan is not None:
        terms.append(f"vlan={value.vlan}")
    if value.protocol is not None:
        terms.append(f"protocol={value.protocol.value}")
    terms += _port_text("srcPort", value.src_ports)
    terms += _port_text("dstPort", value.dst_ports)
    return ",".join(terms)


def _check_classifier(value: QosClassifier | None) -> QosClassifier | None:
    if value is None:
        return None
    if not isinstance(value, QosClassifier):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(f"QosRule.classifier takes a QosClassifier or None, not {value!r}")
    if len(value.src_ports) > 1 or len(value.dst_ports) > 1:
        raise ValueError(
            "a QoS rule's text holds one port range per direction, so a classifier of "
            "a QosRule takes at most one source and one destination range"
        )
    if value == QosClassifier():
        return None  # no restriction: the same as no classifier
    return value


_QOS_PAIRS = (
    SyncedField[QosClassifier | None](
        "match",
        "classifier",
        _parse_classifier,
        _format_classifier,
        _check_classifier,
        "",
        keep_text=True,
    ),
)


@dataclass
class QosRule:
    """A QoS classification rule (classifier -> DSCP/CoS marking).

    ``classifier`` selects the traffic, a :class:`QosClassifier` (VLAN, protocol,
    source and destination port), or ``None`` for every frame or for an expression
    that is not one of those. The driver maps it to its product's QoS classifier;
    ``dscp`` and ``cos`` are the resulting mark values. A rule of this model holds
    at most one source and one destination port range (``ValueError`` otherwise).

    ``match`` is the released spelling, a vendor-neutral classifier expression held
    as text (``""`` for every frame), deprecated. The released contract gave it no
    grammar, so free text is legal and has no classifier: ``classifier`` is
    ``None`` and ``match`` stays exactly as given, nothing lost. A comma list of
    ``key=value`` terms for a VLAN, a protocol (any letter case, ``any`` included),
    source ports and destination ports (a port or an ``a-b`` range) has a classifier;
    a repeated term raises ``ValueError``. The two fields always agree. At
    construction the classifier fills the text; the text alone warns
    (``DeprecationWarning``) and fills the classifier; both given and disagreeing
    raise ``ValueError``. Afterwards, through ``dataclasses.replace`` and through
    assignment, the side that changed wins: setting ``classifier`` writes canonical
    text, while text that parses keeps the spelling it was given. A non-text
    ``match`` or a non-``QosClassifier`` ``classifier`` raises ``TypeError``.
    """

    name: str
    match: str = ""
    dscp: int | None = None
    cos: int | None = None
    classifier: QosClassifier | None = field(default=None, kw_only=True)
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
