"""Firewall-domain data models.

Shared across the ``packet_filter``, ``firewall``, ``nat``,
``conntrack``, ``firewall_zones``, and ``sdwan_policy_manager`` templates.
Transport-agnostic: drivers translate these structures into iptables /
nftables / pf / TR-069 / vendor CLI as appropriate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from testprotocols.models.ports import PortRange
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
    ALERT = "alert"
    """Raise an alert for a matching packet. A released implementer reports this value."""


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


@dataclass(frozen=True)
class RuleCounters:
    """What a rule has matched since it was added.

    *packets* and *bytes* are non-negative ints. Returned by
    ``PacketFilter.get_rule_counter_values`` and
    ``Nat.get_nat_rule_counter_values``.
    """

    packets: int
    bytes: int


@dataclass
class FirewallRule:
    """Holds a stateless or stateful packet-filter rule with match criteria and action.

    Used by the ``packet_filter`` and ``firewall`` templates (per-chain
    rule lists). The IPv4 / IPv6 split is not a contract dimension
    — each rule's address family is inferred from its CIDR fields.

    *action* is a :class:`FirewallRuleAction` (``allow``, ``deny``, ``reject``,
    ``log``) and *protocol* a :class:`~testprotocols.models.RuleProtocol`
    (``tcp``, ``udp``, ``icmp``, ``any``; also ``icmp6``). A plain ``str`` naming
    one is accepted and stored as given (a member compares equal to its text); each
    field narrows to its enum when the plain ``str`` form is removed.

    The destination ports have two forms. *dst_ports* is a tuple of
    :class:`~testprotocols.models.PortRange`, the empty tuple meaning any port.
    *dst_port* is the released text form (a port number, a range like
    ``"1024-65535"``, a comma list, or ``"any"``), deprecated. A driver fills either
    field, or both; when both are filled they describe the same ports. At least one
    is filled: *dst_port* stays required, and a driver that fills only *dst_ports*
    passes ``dst_port=None``. At removal, *dst_port* goes and *dst_ports* becomes required.

    A rule also flows into a driver (``PacketFilter.add_rule``). A caller building one
    for a write member fills both forms until removal: a driver not yet updated reads
    only *dst_port*. A driver implementing a write member reads *dst_ports* when it is
    filled, else *dst_port*.

    *application* / *application_category* are L7 classifiers used by
    SD-WAN policy; they are ignored by simple packet-filter drivers.
    """

    name: str
    action: FirewallRuleAction | str
    protocol: RuleProtocol | str
    src_cidr: str
    dst_cidr: str
    dst_port: str | None
    application: str | None = None
    application_category: str | None = None
    log: bool = True
    dst_ports: tuple[PortRange, ...] | None = field(default=None, kw_only=True)


@dataclass
class NatRule:
    """A NAT translation rule.

    Three modes are supported via the *mode* discriminator, a :class:`NatMode`.
    *protocol* is a :class:`~testprotocols.models.RuleProtocol`. For each, a plain
    ``str`` naming a member is accepted and stored as given; the field narrows to its
    enum when the plain ``str`` form is removed.

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

    The ports have two forms each: *dst_ports* (the match) and *translated_ports*
    (the rewrite) are tuples of :class:`~testprotocols.models.PortRange`, the empty
    tuple meaning no port (any, for the match). *dst_port* and *translated_port*
    are the released text forms (``""`` for no port, also ``"any"``, a port number,
    a range, or a comma list), deprecated. A driver fills either field of a pair, or
    both; when both are filled they describe the same ports. *dst_port* and
    *translated_port* keep their released default ``""`` (no port); a driver that fills
    only the typed form may pass ``None`` for the text, which reads as that default. At
    removal, the text fields go and the typed fields default to ``()``, the typed form of
    the released default, so a rule that never sets them keeps its meaning.

    A rule also flows into a driver (``Nat.add_nat_rule``). A caller building one for a
    write member fills both forms until removal: a driver not yet updated reads only the
    text. A driver implementing a write member reads the typed form when it is filled,
    else the text. A caller that fills only the typed form leaves the text at its
    released default ``""``, and a driver not yet updated acts on that: no port.

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
    protocol: RuleProtocol | str = "any"
    src_cidr: str = ""
    dst_cidr: str = ""
    dst_port: str | None = ""
    translated_src: str = ""
    translated_dst: str = ""
    translated_port: str | None = ""
    enabled: bool = True
    dst_ports: tuple[PortRange, ...] | None = field(default=None, kw_only=True)
    translated_ports: tuple[PortRange, ...] | None = field(default=None, kw_only=True)


@dataclass
class PortMapping:
    """A named external-port → internal-host:port mapping.

    Higher-level than ``NatRule``: drivers may lower a ``PortMapping`` to
    a DNAT primitive, a TR-069 ``Device.NAT.PortMapping`` object, a
    UPnP-IGD / PCP entry, or a vendor port-forward CLI — tests never
    need to know which.

    *protocol* is a :class:`PortMappingProtocol` (``tcp``, ``udp``,
    ``tcp-udp``). A plain ``str`` naming one is accepted and stored as given.
    Deprecated: the plain ``str`` form of *protocol*; the field narrows to
    :class:`PortMappingProtocol`. Removal not before the first release 6 months after the
    release that deprecates it.
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


@dataclass
class Connection:
    """A single tracked connection / flow as observed by the conntrack template.

    Direction is original → reply. *bytes_orig* / *packets_orig* count
    the original direction; *bytes_reply* / *packets_reply* count the
    reverse path.

    *protocol* is a :class:`~testprotocols.models.RuleProtocol`, never ``ANY``: a
    flow has one transport. A plain ``str`` naming a member is accepted and stored as
    given; the field narrows to :class:`~testprotocols.models.RuleProtocol` when the
    plain ``str`` form is removed. *state* is the device's own word and is stored as
    given. It is protocol-specific, for example:

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
