"""Firewall-domain data models.

Shared across the ``packet_filter``, ``firewall``, ``nat``,
``conntrack``, ``firewall_zones``, and ``sdwan_policy_manager`` templates.
Transport-agnostic: drivers translate these structures into iptables /
nftables / pf / TR-069 / vendor CLI as appropriate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import cast, override

from testprotocols.deprecation import MODEL_FRAMES, coerce_enum
from testprotocols.models._sync import SyncedField, assign, settle
from testprotocols.models.ports import (
    PortRange,
    format_port_ranges,
    parse_port_ranges,
    port_tuple,
)
from testprotocols.models.sdwan_appliance import RuleProtocol


class DefaultAction(StrEnum):
    """What a zone or zone pair does with traffic no rule decides."""

    ACCEPT = "accept"
    DROP = "drop"
    REJECT = "reject"


class Chain(StrEnum):
    """A packet-filter chain: the path a packet takes through the device."""

    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    FORWARD = "FORWARD"


class FirewallRuleAction(StrEnum):
    """What a packet-filter rule does with a matching packet."""

    ALLOW = "allow"
    DENY = "deny"
    REJECT = "reject"
    LOG = "log"


class NatMode(StrEnum):
    """The translation a NAT rule performs."""

    SNAT = "snat"
    DNAT = "dnat"
    ONE_TO_ONE = "1to1"


class PortMappingProtocol(StrEnum):
    """The transport a port mapping forwards."""

    TCP = "tcp"
    UDP = "udp"
    TCP_UDP = "tcp-udp"


def _parse_nat_ports(text: str) -> tuple[PortRange, ...]:
    # The released NatRule text for "no port" is the empty string; "any" is also accepted.
    return () if text == "" else parse_port_ranges(text)


def _format_nat_ports(ranges: tuple[PortRange, ...]) -> str:
    return "" if not ranges else format_port_ranges(ranges)


_RULE_PAIRS = (
    SyncedField[tuple[PortRange, ...]](
        "dst_port", "dst_ports", parse_port_ranges, format_port_ranges, port_tuple, "any"
    ),
)
_NAT_PAIRS = tuple(
    SyncedField[tuple[PortRange, ...]](
        old, new, _parse_nat_ports, _format_nat_ports, port_tuple, ""
    )
    for old, new in (("dst_port", "dst_ports"), ("translated_port", "translated_ports"))
)

_RULE_ENUMS: dict[str, type[StrEnum]] = {"action": FirewallRuleAction, "protocol": RuleProtocol}
_NAT_ENUMS: dict[str, type[StrEnum]] = {"mode": NatMode, "protocol": RuleProtocol}
_MAPPING_ENUMS: dict[str, type[StrEnum]] = {"protocol": PortMappingProtocol}
_CONN_ENUMS: dict[str, type[StrEnum]] = {"protocol": RuleProtocol}


def _coerce_field(owner: str, name: str, value: object, enums: dict[str, type[StrEnum]]) -> object:
    """*value* converted when *name* is one of *enums*' fields; otherwise unchanged."""
    enum_type = enums.get(name)
    if enum_type is None:
        return value
    return coerce_enum(
        enum_type,
        cast("StrEnum | str", value),
        what=f"{owner}.{name}",
        skip_file_prefixes=MODEL_FRAMES,
    )


def _set(
    obj: object, owner: str, name: str, value: object, enums: dict[str, type[StrEnum]]
) -> None:
    """Assign *name* on *obj*, converting it first when it is one of *enums*' fields."""
    object.__setattr__(obj, name, _coerce_field(owner, name, value, enums))


def _set_synced(
    obj: object,
    owner: str,
    name: str,
    value: object,
    enums: dict[str, type[StrEnum]],
    pairs: tuple[SyncedField[tuple[PortRange, ...]], ...],
) -> None:
    """Assign *name*: a port field re-syncs its pair, an enum field is converted."""
    if name == "_ports_seen" or any(pair.owns(name) for pair in pairs):
        assign(obj, name, value, pairs, "_ports_seen")
    else:
        _set(obj, owner, name, value, enums)


@dataclass(frozen=True)
class RuleCounters:
    """What a rule has matched since it was added.

    *packets* and *bytes* are non-negative ints (a bool, float or other type
    raises ``TypeError``, a negative number ``ValueError``). Returned by
    ``PacketFilter.get_rule_counter_values`` and
    ``Nat.get_nat_rule_counter_values``.
    """

    packets: int
    bytes: int

    def __post_init__(self) -> None:
        for name in ("packets", "bytes"):
            value: object = getattr(self, name)
            if type(value) is not int:
                raise TypeError(f"RuleCounters.{name} must be an int, not {type(value).__name__}")
            if value < 0:
                raise ValueError(f"RuleCounters.{name} must not be negative, got {value}")


@dataclass
class FirewallRule:
    """Holds a stateless or stateful packet-filter rule with match criteria and action.

    Used by the ``packet_filter`` and ``firewall`` templates (per-chain
    rule lists). The IPv4 / IPv6 split is not a contract dimension
    — each rule's address family is inferred from its CIDR fields.

    *action* is a :class:`FirewallRuleAction` (``allow``, ``deny``, ``reject``,
    ``log``) and *protocol* a :class:`~testprotocols.models.RuleProtocol`
    (``tcp``, ``udp``, ``icmp``, ``any``; also ``icmp6``). A plain ``str`` naming
    one is deprecated: it warns and is converted, also on assignment, so a reader
    always holds the enum. Any other string raises ``ValueError``.
    Ports are *dst_ports*: a tuple of :class:`~testprotocols.models.PortRange`, the
    empty tuple meaning any port. *dst_port* is the released text form (a port
    number, a range like ``"1024-65535"``, a comma list, or ``"any"``, its
    default), deprecated; the two always agree, so a reader of either sees the
    same ports. At construction the typed field fills the text; the text alone
    warns (``DeprecationWarning``) and fills the typed field; both given and
    disagreeing raise ``ValueError``. Afterwards, through ``dataclasses.replace``
    and through assignment, the side that changed wins: ``rule.dst_ports = ...``
    rewrites the text, while ``rule.dst_port = "443"`` re-parses the text into the
    typed field and warns. A text normalises to its canonical form (``"22, 80"``
    reads ``"22,80"``); malformed text raises ``ValueError`` and a non-text
    *dst_port* or non-``PortRange`` *dst_ports* raises ``TypeError``.
    *application* / *application_category* are L7 classifiers used by
    SD-WAN policy; they are ignored by simple packet-filter drivers.
    """

    name: str
    action: FirewallRuleAction | str
    protocol: RuleProtocol | str
    src_cidr: str
    dst_cidr: str
    dst_port: str = "any"
    application: str | None = None
    application_category: str | None = None
    log: bool = True
    dst_ports: tuple[PortRange, ...] = field(default=(), kw_only=True)
    _ports_seen: tuple[str, ...] | None = field(
        default=None, kw_only=True, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        settle(self, _RULE_PAIRS, "_ports_seen")

    @override
    def __setattr__(self, name: str, value: object) -> None:
        # Mutable model: the coercion and the port sync run on every assignment, and
        # the generated ``__init__`` (hence ``dataclasses.replace``) assigns through here too.
        _set_synced(self, "FirewallRule", name, value, _RULE_ENUMS, _RULE_PAIRS)


@dataclass
class NatRule:
    """A NAT translation rule.

    Three modes are supported via the *mode* discriminator, a :class:`NatMode`
    (a plain ``str`` naming one is deprecated: it warns and is converted, also on
    assignment; any other string raises ``ValueError``). *protocol* is a
    :class:`~testprotocols.models.RuleProtocol`, with the same rule:

    - ``"snat"`` — source-NAT (rewrite source on egress). Requires
      *translated_src* (or empty string to fall back to the egress
      interface address). *translated_dst* and *translated_port* must
      be empty.
    - ``"dnat"`` — destination-NAT / port-forward primitive (rewrite
      destination on ingress). Requires *translated_dst*; *translated_port*
      is optional. *translated_src* must be empty.
    - ``"1to1"`` — bidirectional one-to-one NAT (static mapping between
      an outside and inside address). Requires *translated_dst* (the
      inside address). Port fields must be empty.

    Ports are *dst_ports* (the match) and *translated_ports* (the rewrite): tuples
    of :class:`~testprotocols.models.PortRange`, the empty tuple meaning no port
    (any, for the match). *dst_port* and *translated_port* are the released text
    forms (``""`` by default, also ``"any"``, a port number, a range, or a comma
    list), deprecated; each pair always agrees and follows the rule of
    :class:`FirewallRule`'s ports (typed fills text; text alone warns and fills
    typed; disagreeing raises ``ValueError``; the side that changed wins under
    ``replace`` and assignment). The canonical text of no port is ``""``, so
    ``"any"`` reads back as ``""``.

    ``src_cidr`` / ``dst_cidr`` ``""`` and ``translated_src`` / ``translated_dst``
    ``""`` will become ``str | None``, with ``None`` meaning absent; ``""`` means
    absent until then.

    Match criteria default to ``""`` meaning "any". *interface* is the
    egress interface for snat / 1to1, the ingress interface for dnat;
    drivers may also accept a logical name resolved via ``IpInterface``.
    """

    name: str
    mode: NatMode | str
    interface: str
    protocol: RuleProtocol | str = RuleProtocol.ANY
    src_cidr: str = ""
    dst_cidr: str = ""
    dst_port: str = ""
    translated_src: str = ""
    translated_dst: str = ""
    translated_port: str = ""
    enabled: bool = True
    dst_ports: tuple[PortRange, ...] = field(default=(), kw_only=True)
    translated_ports: tuple[PortRange, ...] = field(default=(), kw_only=True)
    _ports_seen: tuple[str, ...] | None = field(
        default=None, kw_only=True, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        settle(self, _NAT_PAIRS, "_ports_seen")

    @override
    def __setattr__(self, name: str, value: object) -> None:
        _set_synced(self, "NatRule", name, value, _NAT_ENUMS, _NAT_PAIRS)


@dataclass
class PortMapping:
    """A named external-port → internal-host:port mapping.

    Higher-level than ``NatRule``: drivers may lower a ``PortMapping`` to
    a DNAT primitive, a TR-069 ``Device.NAT.PortMapping`` object, a
    UPnP-IGD / PCP entry, or a vendor port-forward CLI — tests never
    need to know which.

    *protocol* is a :class:`PortMappingProtocol` (``tcp``, ``udp``,
    ``tcp-udp``). A plain ``str`` naming one is deprecated: it warns and is
    converted, also on assignment; any other string raises ``ValueError``.
    *external_interface* of ``None`` means "all external interfaces".
    *src_cidr* may restrict the mapping to a specific source range
    (firewall hardening); the default ``"0.0.0.0/0"`` accepts any source.
    """

    name: str
    external_port: int
    protocol: PortMappingProtocol | str
    internal_host: str
    internal_port: int
    external_interface: str | None = None
    src_cidr: str = "0.0.0.0/0"
    description: str = ""
    enabled: bool = True

    @override
    def __setattr__(self, name: str, value: object) -> None:
        _set(self, "PortMapping", name, value, _MAPPING_ENUMS)


@dataclass
class Connection:
    """A single tracked connection / flow as observed by the conntrack template.

    Direction is original → reply. *bytes_orig* / *packets_orig* count
    the original direction; *bytes_reply* / *packets_reply* count the
    reverse path.

    *protocol* is a :class:`~testprotocols.models.RuleProtocol` (never ``ANY``:
    a flow has one transport) and follows the same deprecation rule as the other
    firewall records. *state* is the device's own word and is stored as given. It is
    protocol-specific, for example:

    - TCP: ``SYN_SENT``, ``SYN_RECV``, ``ESTABLISHED``, ``FIN_WAIT``,
      ``CLOSE_WAIT``, ``LAST_ACK``, ``TIME_WAIT``, ``CLOSE``, ``LISTEN``.
    - UDP / ICMP / other: ``UNREPLIED``, ``ASSURED``, or a driver-specific
      state.

    *translated_src* / *translated_dst* are populated (non-None) when NAT
    is altering this flow. *src_port* / *dst_port* are ``None`` for ICMP.
    """

    protocol: RuleProtocol | str
    src_ip: str
    dst_ip: str
    src_port: int | None
    dst_port: int | None
    state: str
    timeout_seconds: int
    bytes_orig: int
    bytes_reply: int
    packets_orig: int
    packets_reply: int
    translated_src: str | None = None
    translated_dst: str | None = None
    mark: int | None = None
    zone: str | None = None

    @override
    def __setattr__(self, name: str, value: object) -> None:
        value = _coerce_field("Connection", name, value, _CONN_ENUMS)
        if value is RuleProtocol.ANY:
            raise ValueError("Connection.protocol: a flow has one transport, not 'any'")
        object.__setattr__(self, name, value)


@dataclass
class ConntrackStats:
    """Conntrack table-level aggregate counters.

    *count* and *max* are the only universally available values; the
    remaining fields are populated where the driver can report them.
    ``None`` means "driver does not expose this counter", not zero.
    """

    count: int
    max: int
    inserted: int | None = None
    deleted: int | None = None
    drops: int | None = None
    early_drops: int | None = None
    invalid: int | None = None
    search_restarts: int | None = None


@dataclass
class Zone:
    """A named firewall zone — a group of interfaces and / or networks
    sharing default-input / default-forward / default-output policy.

    Models the OpenWrt-style zone model (also maps to firewalld zones,
    pfSense interface groups, etc.). Empty *interfaces* and *networks*
    lists are valid (zone exists but is not yet bound).

    *default_input* / *default_forward* / *default_output* are one of
    ``"accept"``, ``"drop"``, ``"reject"`` and govern traffic that
    doesn't match any explicit rule. *masquerade* enables auto-SNAT on
    egress traffic from this zone; *mss_clamping* enables PMTU clamping
    (helpful on PPPoE WAN zones).
    """

    name: str
    interfaces: list[str] = field(default_factory=list[str])
    networks: list[str] = field(default_factory=list[str])
    default_input: str = "drop"
    default_forward: str = "drop"
    default_output: str = "accept"
    masquerade: bool = False
    mss_clamping: bool = False


@dataclass
class ZonePolicy:
    """Default forwarding action between two zones.

    Models the per-zone-pair forwarding link in OpenWrt-style firewalls.
    More specific traffic between the same pair is still controlled by
    ``FirewallRule`` records (in ``packet_filter`` or ``firewall``);
    this is the fall-through.

    *action* is one of ``"accept"``, ``"drop"``, ``"reject"``.
    """

    src_zone: str
    dst_zone: str
    action: str
