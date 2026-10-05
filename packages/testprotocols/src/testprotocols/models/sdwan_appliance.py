"""Data models for the vendor-neutral SD-WAN **appliance** capabilities.

These back the managed-appliance capability protocols composed by
``devices.sdwan.SdwanApplianceDevice`` (distinct from the Linux digital twin's
``SdwanRouterDevice``).

**Vendor neutrality is part of the contract.** Field value-vocabularies are
*normalized* and owned here as ``StrEnum`` types: members are plain strings (so
serialization to a vendor's REST/JSON API is trivial), constructing from a value
validates it (``RuleAction("x")`` raises ``ValueError``), and the types give
static checking at every driver/test call site. A testbed plugin maps its
product's representation to/from these neutral values; no vendor identifier, raw
payload, or vendor-specific vocabulary ever appears in this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from testprotocols.models.ports import PortRange


class RuleAction(StrEnum):
    """Action a firewall rule takes on a match."""

    ALLOW = "allow"
    DENY = "deny"


class RuleProtocol(StrEnum):
    """Transport a rule matches. ``ANY`` leaves the protocol unconstrained."""

    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    ICMP6 = "icmp6"
    ANY = "any"


@dataclass
class L3Rule:
    """A single ordered L3 firewall rule — 5-tuple match plus an action.

    A managed appliance evaluates its L3 policy as a flat, ordered list of these
    (not as netfilter INPUT/OUTPUT/FORWARD chains). The CIDR fields take
    ``"any"`` when unconstrained.

    The ports have two forms each. ``src_ports`` and ``dst_ports`` are tuples of
    :class:`PortRange`, the empty tuple meaning any port. ``src_port`` and
    ``dst_port`` are the released text forms (``"any"``, a port, a range such as
    ``"8000-8100"``, or a comma list), deprecated. A driver fills either field of a
    pair, or both; when both are filled they describe the same ports. A pair left
    unfilled (``None``) means what the released default ``"any"`` meant: any port. At
    removal, the text fields go and the typed fields become required.

    ``src_cidr`` and ``dst_cidr`` ``"any"`` will become ``str | None``, with
    ``None`` meaning unconstrained; ``"any"`` means unconstrained until then.

    ``syslog_enabled`` is per-rule intent. Products whose firewall logging is
    only list- or segment-scoped approximate it in the driver (enable scoped
    logging when any rule requests it) — an accepted, documented approximation,
    not a contract violation.
    """

    action: RuleAction
    protocol: RuleProtocol = RuleProtocol.ANY
    src_cidr: str = "any"
    src_port: str | None = None
    dst_cidr: str = "any"
    dst_port: str | None = None
    comment: str = ""
    syslog_enabled: bool = False
    src_ports: tuple[PortRange, ...] | None = field(default=None, kw_only=True)
    dst_ports: tuple[PortRange, ...] | None = field(default=None, kw_only=True)


class L7MatchType(StrEnum):
    """How an L7 (application-aware) firewall rule selects traffic."""

    APPLICATION = "application"
    APPLICATION_CATEGORY = "application_category"
    HOST = "host"
    PORT = "port"
    IP_RANGE = "ip_range"


@dataclass
class L7Rule:
    """A single application-aware (L7) firewall rule.

    ``match_type`` selects the dimension; ``value`` carries the matched item.
    For ``HOST`` / ``PORT`` / ``IP_RANGE`` the value is a free string. For
    ``APPLICATION_CATEGORY`` the value is an ``ApplicationCategory`` member. For
    ``APPLICATION`` (an individual app) the value is a vendor-mapped string — a
    normalized ``Application`` registry is not seeded yet (grow on evidence). The
    driver maps the value to its product's identifier in all cases.
    """

    action: RuleAction
    match_type: L7MatchType
    value: str
    comment: str = ""


class ContentCategory(StrEnum):
    """Normalized URL / content-filtering categories owned by commons.

    A balanced **standard** set drawn from the common-denominator categories
    across managed SD-WAN appliances' URL-filter taxonomies — broad enough to
    cover the likely need without mirroring any one vendor's full list. The
    plugin maps each to its product's category id; add members on evidence.
    """

    ADULT = "adult"
    ADVERTISING = "advertising"
    ALCOHOL_AND_TOBACCO = "alcohol_and_tobacco"
    BUSINESS = "business"
    DATING = "dating"
    DRUGS = "drugs"
    EDUCATION = "education"
    FILE_SHARING = "file_sharing"
    FINANCE = "finance"
    GAMBLING = "gambling"
    GAMES = "games"
    GOVERNMENT = "government"
    HACKING = "hacking"
    HEALTH = "health"
    ILLEGAL_CONTENT = "illegal_content"
    JOB_SEARCH = "job_search"
    MALWARE_SITES = "malware_sites"
    NEWS = "news"
    PEER_TO_PEER = "peer_to_peer"
    PHISHING = "phishing"
    RELIGION = "religion"
    SEARCH_ENGINES = "search_engines"
    SHOPPING = "shopping"
    SOCIAL_NETWORKING = "social_networking"
    SPORTS = "sports"
    STREAMING_MEDIA = "streaming_media"
    TRAVEL = "travel"
    VIOLENCE = "violence"
    WEAPONS = "weapons"
    WEB_BASED_EMAIL = "web_based_email"


@dataclass(frozen=True)
class UrlRules:
    """A content filter's explicit URL-pattern lists: *allowed* and *blocked*.

    Patterns are free strings (host or glob patterns), as the appliance holds them.
    """

    allowed: tuple[str, ...] = ()
    blocked: tuple[str, ...] = ()


class ApplicationCategory(StrEnum):
    """Normalized application categories for L7 (application-aware) policy.

    A balanced **standard** set drawn from the common-denominator app-control
    categories across managed SD-WAN appliances — the dimensions a test is
    likely to steer or block on. The plugin maps each to its product's
    application-category id; add members on evidence. (Individual application
    identifiers — a far larger, more divergent catalog — are deliberately not
    seeded here; add an ``Application`` registry if/when a test needs one.)

    ``AppFlow.category`` is the product's own word as text, so a flow whose
    category this set does not list is still reported.
    """

    ADVERTISING = "advertising"
    BUSINESS_AND_PRODUCTIVITY = "business_and_productivity"
    CLOUD_SERVICES = "cloud_services"
    COLLABORATION = "collaboration"
    DATABASE = "database"
    EMAIL = "email"
    FILE_SHARING = "file_sharing"
    GAMING = "gaming"
    INSTANT_MESSAGING = "instant_messaging"
    MUSIC_STREAMING = "music_streaming"
    NETWORK_SERVICES = "network_services"
    NEWS = "news"
    PEER_TO_PEER = "peer_to_peer"
    REMOTE_ACCESS = "remote_access"
    SOCIAL_NETWORKING = "social_networking"
    SOFTWARE_UPDATES = "software_updates"
    SPORTS = "sports"
    VIDEO_STREAMING = "video_streaming"
    VOIP_AND_VIDEO_CONFERENCING = "voip_and_video_conferencing"
    VPN_AND_PROXY = "vpn_and_proxy"
    WEB_FILE_TRANSFER = "web_file_transfer"


# --- Traffic match (what an L7 or shaping rule selects) ---


@dataclass(frozen=True)
class ApplicationMatch:
    """Traffic of one application, by its vendor-mapped name (an open name: a
    normalized application registry is not seeded; grow on evidence). The name is
    not empty."""

    name: str


@dataclass(frozen=True)
class CategoryMatch:
    """Traffic of one application category."""

    category: ApplicationCategory


@dataclass(frozen=True)
class HostMatch:
    """Traffic to one host, by name. The name is not empty."""

    host: str


@dataclass(frozen=True)
class PortMatch:
    """Traffic to the given ports (at least one :class:`PortRange`)."""

    ports: tuple[PortRange, ...]


@dataclass(frozen=True)
class IpRangeMatch:
    """Traffic to or from an address range: an address prefix
    (``198.51.100.0/24``) or a first-last range (``198.51.100.10-198.51.100.20``).
    A product that matches prefixes only refuses a first-last range per value. The
    range is not empty."""

    cidr: str


TrafficMatch = ApplicationMatch | CategoryMatch | HostMatch | PortMatch | IpRangeMatch
"""What an L7 or shaping rule selects: one of the five match kinds."""


# --- Traffic shaping ---


class ShapingPriority(StrEnum):
    """Relative scheduling priority a shaping rule assigns to matched traffic."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


@dataclass
class ShapingRule:
    """A traffic-shaping rule — match a traffic class, then limit / mark / prioritize.

    ``match_type`` / ``value`` reuse the L7 match vocabulary (by application,
    application category, host, port, or IP range). ``bandwidth_limit_kbps``
    caps the class (``None`` = uncapped); ``dscp_tag`` applies a DSCP marking
    (``None`` = leave unmarked); ``priority`` sets relative scheduling.
    """

    name: str
    match_type: L7MatchType
    value: str
    bandwidth_limit_kbps: int | None = None
    dscp_tag: int | None = None
    priority: ShapingPriority = ShapingPriority.NORMAL


# --- NAT (1:1 / 1:Many / port-forwarding) ---


@dataclass
class NatInboundAllow:
    """An inbound allowance attached to a 1:1 NAT mapping."""

    protocol: RuleProtocol = RuleProtocol.ANY
    ports: str = "any"
    allowed_remote_cidrs: list[str] = field(default_factory=lambda: ["any"])


@dataclass
class PortForwardRule:
    """A port-forwarding (DNAT) rule — public port → internal host:port."""

    name: str
    protocol: RuleProtocol
    public_port: str
    lan_ip: str
    local_port: str
    uplink: str = "any"
    allowed_remote_cidrs: list[str] = field(default_factory=lambda: ["any"])


@dataclass
class OneToOneNatRule:
    """A 1:1 NAT mapping between a public IP and an internal IP."""

    name: str
    public_ip: str
    lan_ip: str
    uplink: str = "any"
    allowed_inbound: list[NatInboundAllow] = field(default_factory=list[NatInboundAllow])


@dataclass
class OneToManyNatRule:
    """A 1:many (PAT) mapping — one public IP, many port-based forwards."""

    public_ip: str
    uplink: str = "any"
    port_forwards: list[PortForwardRule] = field(default_factory=list[PortForwardRule])


# --- WAN uplinks ---


class UplinkState(StrEnum):
    """Operational state of a WAN uplink.

    ``DEGRADED`` covers vendor states reporting a link that is forwarding but
    impaired (unstable / lossy / connecting) — normalized here so drivers do
    not collapse such states into ``UP``. ``UNKNOWN`` is a state the product could
    not determine (for example a link with no health data yet), distinct from
    ``DOWN``.
    """

    UP = "up"
    DEGRADED = "degraded"
    DOWN = "down"
    STANDBY = "standby"
    NOT_CONNECTED = "not_connected"
    UNKNOWN = "unknown"


@dataclass
class UplinkStatus:
    """Current status of a single WAN uplink (read-only observation).

    ``ip``, ``gateway``, ``public_ip`` and ``primary_dns`` are ``""`` when the
    product does not report them; they will become ``str | None``, with ``None``
    meaning not reported, and ``""`` means not reported until then.
    """

    name: str
    state: UplinkState
    ip: str = ""
    gateway: str = ""
    public_ip: str = ""
    primary_dns: str = ""


# --- Syslog destinations ---


class SyslogRole(StrEnum):
    """Category of log a syslog destination receives."""

    EVENT_LOG = "event_log"
    FLOWS = "flows"
    SECURITY = "security"
    URLS = "urls"


@dataclass
class SyslogServer:
    """A syslog destination and the log roles it receives."""

    host: str
    port: int = 514
    roles: list[SyslogRole] = field(default_factory=list[SyslogRole])


# --- Threat prevention (IDS / IPS + malware) ---


class IntrusionMode(StrEnum):
    """IDS/IPS operating mode."""

    DISABLED = "disabled"
    DETECTION = "detection"
    PREVENTION = "prevention"


class IntrusionSensitivity(StrEnum):
    """Normalized IPS ruleset sensitivity (vendor ruleset names map onto this)."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MalwareMode(StrEnum):
    """Anti-malware operating mode."""

    DISABLED = "disabled"
    ENABLED = "enabled"


class SecurityAction(StrEnum):
    """What the appliance did about a security event."""

    ALLOWED = "allowed"
    BLOCKED = "blocked"
    DETECTED = "detected"


class ThreatCategory(StrEnum):
    """Normalized class of a security event."""

    MALWARE = "malware"
    INTRUSION = "intrusion"
    EXPLOIT = "exploit"
    SCAN = "scan"
    BOTNET = "botnet"
    PHISHING = "phishing"
    POLICY_VIOLATION = "policy_violation"


@dataclass
class IntrusionConfig:
    """IDS/IPS configuration state."""

    mode: IntrusionMode
    sensitivity: IntrusionSensitivity | None = None


@dataclass
class MalwareConfig:
    """Anti-malware configuration state."""

    mode: MalwareMode


@dataclass
class SecurityEvent:
    """A normalized security event (the deferred-API-augmentation surface).

    Carries only normalized fields for portable assertions — vendor signature
    ids and raw payloads are deliberately not modelled.

    The time of the event has two forms. ``timestamp`` is when the event happened, a
    :class:`~datetime.datetime`, or ``None`` when the product reports no time; a
    timezone-naive value stays naive (no zone is assumed). ``ts`` is the released text
    form, an ISO-8601 timestamp string (``""`` for none), deprecated. A driver fills
    either field, or both; when both are filled they describe the same instant. At
    least one is filled: ``ts`` stays required, and a driver that fills only
    ``timestamp`` passes ``ts=None`` (``timestamp=None`` is then the value "no time
    reported"). At removal, ``ts`` goes and ``timestamp`` becomes required.
    """

    ts: str | None
    src_ip: str
    dst_ip: str
    protocol: RuleProtocol
    action: SecurityAction
    category: ThreatCategory
    description: str = ""
    timestamp: datetime | None = field(default=None, kw_only=True)


# --- LAN VLANs + DHCP ---


class DhcpMode(StrEnum):
    """How the appliance handles DHCP on a VLAN."""

    SERVER = "server"
    RELAY = "relay"
    DISABLED = "disabled"


class DhcpOptionType(StrEnum):
    """Value type of a DHCP option."""

    TEXT = "text"
    IP = "ip"
    INTEGER = "integer"
    HEX = "hex"


@dataclass
class DhcpOption:
    """A custom DHCP option served on a VLAN."""

    code: int
    type: DhcpOptionType
    value: str


@dataclass
class DhcpReservation:
    """A fixed IP assignment for a known MAC."""

    mac: str
    ip: str
    name: str = ""


@dataclass
class ReservedRange:
    """An address range excluded from a DHCP pool.

    ``comment`` is the free-text label some platforms keep with the range. It
    is optional here: a driver whose management plane requires a label
    supplies or enforces one at its own boundary, never through this model.
    """

    start: str
    end: str
    comment: str = ""


@dataclass
class VlanConfig:
    """A LAN VLAN and its DHCP configuration.

    ``dhcp_lease_seconds`` normalizes lease time to seconds (vendors express it
    variously). ``dns_servers`` empty means "use the appliance / upstream
    default". ``reserved_ranges`` are :class:`ReservedRange` records excluded
    from the dynamic pool, each carrying its optional label.
    """

    vlan_id: int
    name: str
    subnet: str
    appliance_ip: str
    dhcp_mode: DhcpMode = DhcpMode.SERVER
    dhcp_lease_seconds: int = 86400
    dns_servers: list[str] = field(default_factory=list[str])
    dhcp_options: list[DhcpOption] = field(default_factory=list[DhcpOption])
    reservations: list[DhcpReservation] = field(default_factory=list[DhcpReservation])
    reserved_ranges: list[ReservedRange] = field(default_factory=list[ReservedRange])


@dataclass
class DhcpLease:
    """An observed DHCP lease (read-only)."""

    mac: str
    ip: str
    hostname: str = ""
    vlan_id: int = 0


# --- Site-to-site VPN overlay ---


class VpnRole(StrEnum):
    """Role a device plays in the site-to-site VPN overlay."""

    DISABLED = "disabled"
    HUB = "hub"
    SPOKE = "spoke"


class VpnPeerState(StrEnum):
    """Reachability of a site-to-site VPN peer."""

    REACHABLE = "reachable"
    UNREACHABLE = "unreachable"
    UNKNOWN = "unknown"


@dataclass
class VpnHub:
    """A hub a spoke connects to.

    ``name`` is the testbed-level hub identifier; the plugin maps it to the
    vendor's id. ``use_default_route`` points the spoke's default route into
    the overlay via this hub.
    """

    name: str
    use_default_route: bool = False


@dataclass
class VpnSubnet:
    """A local subnet and whether it participates in the overlay."""

    subnet: str
    advertise: bool = True


@dataclass
class SiteToSiteVpnConfig:
    """Complete overlay-participation config — read and replaced whole.

    ``hubs`` is only meaningful for ``VpnRole.SPOKE`` and is ordered by
    priority. ``subnets`` lists the local subnets and whether each is
    advertised into the overlay.
    """

    role: VpnRole
    hubs: list[VpnHub] = field(default_factory=list[VpnHub])
    subnets: list[VpnSubnet] = field(default_factory=list[VpnSubnet])


@dataclass
class VpnPeerStatus:
    """Observed status of one site-to-site VPN peer (read-only).

    ``name`` is the peer's testbed-level site name (normalized; the plugin
    maps the vendor's peer identifier). ``uplink`` names the local uplink
    carrying the tunnel when the product reports it, else ``""``.
    """

    name: str
    state: VpnPeerState
    uplink: str = ""


# --- Path steering (uplink selection) ---


class SteeringScope(StrEnum):
    """Traffic domain an uplink-selection rule steers.

    Deliberately no ``ANY`` member — the test author states the intent, and
    products with split steering surfaces need it to route the write.
    """

    INTERNET = "internet"
    OVERLAY = "overlay"


@dataclass
class FlowMatch:
    """5-tuple traffic match for steering rules (match only — no action).

    Field semantics mirror ``L3Rule``'s match half: ``"any"`` when
    unconstrained; ports may be a single port, a range (``"8000-8100"``),
    or a comma list.
    """

    protocol: RuleProtocol = RuleProtocol.ANY
    src_cidr: str = "any"
    src_port: str = "any"
    dst_cidr: str = "any"
    dst_port: str = "any"


@dataclass
class UplinkSelectionRule:
    """One ordered uplink-steering rule.

    With ``performance_class`` set (the *name* of an ``SLAPolicy`` configured
    via ``configure_sla_policy``), traffic matching ``match`` is steered to
    ``preferred_uplink`` while the class is met and fails over when it is
    breached. With ``performance_class=None`` the preference is static —
    failover occurs only on uplink loss.
    """

    name: str
    scope: SteeringScope
    match: FlowMatch
    preferred_uplink: str
    performance_class: str | None = None


@dataclass(frozen=True)
class UplinkSelectionSettings:
    """The scalar half of the uplink-selection surface (read-only snapshot).

    The network-wide settings that frame the ordered rule list: which uplink
    carries default-routed traffic, whether load balancing across uplinks is
    on, and whether the overlay runs tunnels over all active uplinks
    concurrently (``active_active_vpn`` — a prerequisite on some products for
    performance-class steering to evaluate at all). Frozen: a captured
    snapshot is a restore target, so it must not mutate after capture.
    """

    default_uplink: str
    load_balancing_enabled: bool
    active_active_vpn: bool


# --- Static routes ---


@dataclass
class StaticRoute:
    """A testbed-owned static route.

    ``name`` is the per-entry CRUD handle (``remove_static_route(name)``).
    Products whose API keys routes by sequence number or opaque id carry the
    name in their description/comment field or a driver-side mapping — a
    driver concern, not a contract one. ``next_hop`` is a next-hop IP
    address; interface-bound next hops, metrics/administrative distance, and
    per-route advertise flags grow on evidence.
    """

    name: str
    destination_cidr: str
    next_hop: str


# --- BGP ---


class BgpSessionState(StrEnum):
    """BGP FSM state of a neighbor session.

    The RFC 4271 state vocabulary — protocol-standard, not vendor-specific,
    so the full set is seeded (the grow-on-evidence rule applies to vendor
    taxonomies, not to standardized protocol states). ``UNKNOWN`` absorbs
    vendor representations that do not map to an FSM state.
    """

    IDLE = "idle"
    CONNECT = "connect"
    ACTIVE = "active"
    OPEN_SENT = "open_sent"
    OPEN_CONFIRM = "open_confirm"
    ESTABLISHED = "established"
    UNKNOWN = "unknown"


@dataclass
class BgpNeighbor:
    """A configured BGP neighbor (minimal — timers/auth/multihop grow on
    evidence)."""

    peer_ip: str
    remote_as: int


@dataclass
class BgpConfig:
    """Complete BGP configuration — read and replaced whole.

    ``enabled`` / ``as_number`` / ``neighbors`` are semantically coupled,
    and most reviewed management planes expose BGP as one object, so the
    surface is whole-config replace (idempotent), not per-neighbor CRUD.
    ``advertised_networks`` lists CIDRs announced to peers; products that
    auto-advertise their overlay subnets and offer no per-network control
    raise unsupported-capability when it is non-empty.
    """

    enabled: bool
    as_number: int
    neighbors: list[BgpNeighbor] = field(default_factory=list[BgpNeighbor])
    advertised_networks: list[str] = field(default_factory=list[str])


@dataclass
class BgpPeerStatus:
    """Observed status of one BGP neighbor session (read-only).

    ``prefixes_received`` is ``None`` when the product does not report a
    count.
    """

    peer_ip: str
    remote_as: int
    state: BgpSessionState
    prefixes_received: int | None = None
