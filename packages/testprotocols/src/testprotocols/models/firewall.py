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
from testprotocols.models._open_enum import OpenEnumPair
from testprotocols.models._sync import assign, settle
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


class ConnState(StrEnum):
    """The state of a tracked connection. The set is open: ``OTHER`` stands for a
    state this enum does not name, and the device's own word is kept in
    ``Connection.state_raw``.

    The values are the words the released contract listed, in upper case: the nine
    TCP states and the two datagram states (``UNREPLIED``, ``ASSURED``), so a reader
    comparing ``conn.state == "ESTABLISHED"`` is unchanged.
    """

    SYN_SENT = "SYN_SENT"
    SYN_RECV = "SYN_RECV"
    ESTABLISHED = "ESTABLISHED"
    FIN_WAIT = "FIN_WAIT"
    CLOSE_WAIT = "CLOSE_WAIT"
    LAST_ACK = "LAST_ACK"
    TIME_WAIT = "TIME_WAIT"
    CLOSE = "CLOSE"
    LISTEN = "LISTEN"
    UNREPLIED = "UNREPLIED"
    ASSURED = "ASSURED"
    OTHER = "OTHER"


_STATE_PAIRS = (OpenEnumPair(ConnState, ConnState.OTHER, "state", "state_raw"),)

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
    *dst_port* is a port number, a range like ``"1024-65535"``, or ``"any"``.
    *application* / *application_category* are L7 classifiers used by
    SD-WAN policy; they are ignored by simple packet-filter drivers.
    """

    name: str
    action: FirewallRuleAction | str
    protocol: RuleProtocol | str
    src_cidr: str
    dst_cidr: str
    dst_port: str
    application: str | None = None
    application_category: str | None = None
    log: bool = True

    @override
    def __setattr__(self, name: str, value: object) -> None:
        # Mutable model: the coercion runs on every assignment, and the generated
        # ``__init__`` (hence ``dataclasses.replace``) assigns through here too.
        _set(self, "FirewallRule", name, value, _RULE_ENUMS)


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

    @override
    def __setattr__(self, name: str, value: object) -> None:
        _set(self, "NatRule", name, value, _NAT_ENUMS)


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
    a flow has one transport). *state* is a :class:`ConnState`, protocol-specific:

    - TCP: ``SYN_SENT``, ``SYN_RECV``, ``ESTABLISHED``, ``FIN_WAIT``,
      ``CLOSE_WAIT``, ``LAST_ACK``, ``TIME_WAIT``, ``CLOSE``, ``LISTEN``.
    - UDP / ICMP / other: ``UNREPLIED``, ``ASSURED``, or a driver-specific
      state, which is ``OTHER`` with the device's own word in *state_raw*.

    The set is open, so an unknown string is not an error: it becomes ``OTHER``
    plus *state_raw*, kept verbatim (the empty string and ``"other"`` included)
    and without a warning. A plain ``str`` naming a member (``"ESTABLISHED"``;
    the match is exact, so ``"established"`` is an unknown word) is deprecated: it
    warns and is converted; ``"OTHER"`` converts to ``OTHER`` with no raw word.
    *state_raw* is ``None`` unless *state* is ``OTHER``. The pair agrees after
    construction, ``replace`` and assignment, and the side that changed wins:
    assigning a member clears the raw word, assigning an unknown string sets it,
    assigning only *state_raw* keeps *state*. A raw word given with a named state,
    or one that disagrees with the unknown word *state* was given, raises
    ``ValueError`` and changes nothing. *protocol* may not be
    ``RuleProtocol.ANY`` (``ValueError``) and follows the same deprecation rule
    as the other firewall records.

    *translated_src* / *translated_dst* are populated (non-None) when NAT
    is altering this flow. *src_port* / *dst_port* are ``None`` for ICMP.
    """

    protocol: RuleProtocol | str
    src_ip: str
    dst_ip: str
    src_port: int | None
    dst_port: int | None
    state: ConnState | str
    timeout_seconds: int
    bytes_orig: int
    bytes_reply: int
    packets_orig: int
    packets_reply: int
    translated_src: str | None = None
    translated_dst: str | None = None
    mark: int | None = None
    zone: str | None = None
    state_raw: str | None = None
    _state_seen: tuple[tuple[ConnState, str | None], ...] | None = field(
        default=None, kw_only=True, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        settle(self, _STATE_PAIRS, "_state_seen")

    @override
    def __setattr__(self, name: str, value: object) -> None:
        if name in ("state", "state_raw", "_state_seen"):
            assign(self, name, value, _STATE_PAIRS, "_state_seen")
            return
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
