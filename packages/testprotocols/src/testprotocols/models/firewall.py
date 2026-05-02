"""Firewall-domain data models.

Shared across the ``packet_filter``, ``nat``, ``port_forwarding``,
``conntrack``, ``firewall_zones``, and ``sdwan_policy_manager`` templates.
Transport-agnostic: drivers translate these structures into iptables /
nftables / pf / TR-069 / vendor CLI as appropriate.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FirewallRule:
    """Holds a stateless or stateful packet-filter rule with match criteria and action.

    Used by the ``packet_filter`` template (per-chain rule lists) and by
    ``sdwan_policy_manager.apply_firewall_rule`` (policy-bound application
    classification rules). The IPv4 / IPv6 split is not a contract dimension
    — each rule's address family is inferred from its CIDR fields.

    *action* is one of ``"allow"``, ``"deny"``, ``"reject"``, ``"log"``.
    *protocol* is one of ``"tcp"``, ``"udp"``, ``"icmp"``, ``"any"``.
    *dst_port* is a port number, a range like ``"1024-65535"``, or ``"any"``.
    *application* / *application_category* are L7 classifiers used by
    SD-WAN policy; they are ignored by simple packet-filter drivers.
    """

    name: str
    action: str
    protocol: str
    src_cidr: str
    dst_cidr: str
    dst_port: str
    application: str | None = None
    application_category: str | None = None
    log: bool = True


@dataclass
class NatRule:
    """A NAT translation rule.

    Three modes are supported via the *mode* discriminator:

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
    mode: str
    interface: str
    protocol: str = "any"
    src_cidr: str = ""
    dst_cidr: str = ""
    dst_port: str = ""
    translated_src: str = ""
    translated_dst: str = ""
    translated_port: str = ""
    enabled: bool = True


@dataclass
class PortMapping:
    """A named external-port → internal-host:port mapping.

    Higher-level than ``NatRule``: drivers may lower a ``PortMapping`` to
    a DNAT primitive, a TR-069 ``Device.NAT.PortMapping`` object, a
    UPnP-IGD / PCP entry, or a vendor port-forward CLI — tests never
    need to know which.

    *protocol* is one of ``"tcp"``, ``"udp"``, ``"tcp-udp"``.
    *external_interface* of ``None`` means "all external interfaces".
    *src_cidr* may restrict the mapping to a specific source range
    (firewall hardening); the default ``"0.0.0.0/0"`` accepts any source.
    """

    name: str
    external_port: int
    protocol: str
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

    *state* is protocol-specific:

    - TCP: ``"SYN_SENT"``, ``"SYN_RECV"``, ``"ESTABLISHED"``,
      ``"FIN_WAIT"``, ``"CLOSE_WAIT"``, ``"LAST_ACK"``, ``"TIME_WAIT"``,
      ``"CLOSE"``, ``"LISTEN"``.
    - UDP / ICMP / other: ``"UNREPLIED"``, ``"ASSURED"``, or
      driver-specific values.

    *translated_src* / *translated_dst* are populated (non-None) when NAT
    is altering this flow. *src_port* / *dst_port* are ``None`` for ICMP.
    """

    protocol: str
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
    ``FirewallRule`` records (in ``packet_filter``); this is the
    fall-through.

    *action* is one of ``"accept"``, ``"drop"``, ``"reject"``.
    """

    src_zone: str
    dst_zone: str
    action: str
