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
from enum import StrEnum


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
    (not as netfilter INPUT/OUTPUT/FORWARD chains). The CIDR and port fields take
    ``"any"`` when unconstrained; ports may be a single port, a range
    (``"8000-8100"``), or a comma list — always a string so the contract stays
    transport- and vendor-agnostic.

    ``syslog_enabled`` is per-rule intent. Products whose firewall logging is
    only list- or segment-scoped approximate it in the driver (enable scoped
    logging when any rule requests it) — an accepted, documented approximation,
    not a contract violation.
    """

    action: RuleAction
    protocol: RuleProtocol = RuleProtocol.ANY
    src_cidr: str = "any"
    src_port: str = "any"
    dst_cidr: str = "any"
    dst_port: str = "any"
    comment: str = ""
    syslog_enabled: bool = False


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


class ApplicationCategory(StrEnum):
    """Normalized application categories for L7 (application-aware) policy.

    A balanced **standard** set drawn from the common-denominator app-control
    categories across managed SD-WAN appliances — the dimensions a test is
    likely to steer or block on. The plugin maps each to its product's
    application-category id; add members on evidence. (Individual application
    identifiers — a far larger, more divergent catalog — are deliberately not
    seeded here; add an ``Application`` registry if/when a test needs one.)
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
    allowed_inbound: list[NatInboundAllow] = field(default_factory=list)


@dataclass
class OneToManyNatRule:
    """A 1:many (PAT) mapping — one public IP, many port-based forwards."""

    public_ip: str
    uplink: str = "any"
    port_forwards: list[PortForwardRule] = field(default_factory=list)


# --- WAN uplinks ---


class UplinkState(StrEnum):
    """Operational state of a WAN uplink.

    ``DEGRADED`` covers vendor states reporting a link that is forwarding but
    impaired (unstable / lossy / connecting) — normalized here so drivers do
    not collapse such states into ``UP``.
    """

    UP = "up"
    DEGRADED = "degraded"
    DOWN = "down"
    STANDBY = "standby"
    NOT_CONNECTED = "not_connected"


@dataclass
class UplinkStatus:
    """Current status of a single WAN uplink (read-only observation)."""

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
    roles: list[SyslogRole] = field(default_factory=list)


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
    ids and raw payloads are deliberately not modelled. ``ts`` is an ISO-8601
    UTC timestamp string.
    """

    ts: str
    src_ip: str
    dst_ip: str
    protocol: RuleProtocol
    action: SecurityAction
    category: ThreatCategory
    description: str = ""


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
class VlanConfig:
    """A LAN VLAN and its DHCP configuration.

    ``dhcp_lease_seconds`` normalizes lease time to seconds (vendors express it
    variously). ``dns_servers`` empty means "use the appliance / upstream
    default". Reserved ranges are ``(start_ip, end_ip)`` pairs excluded from
    the dynamic pool.
    """

    vlan_id: int
    name: str
    subnet: str
    appliance_ip: str
    dhcp_mode: DhcpMode = DhcpMode.SERVER
    dhcp_lease_seconds: int = 86400
    dns_servers: list[str] = field(default_factory=list)
    dhcp_options: list[DhcpOption] = field(default_factory=list)
    reservations: list[DhcpReservation] = field(default_factory=list)
    reserved_ranges: list[tuple[str, str]] = field(default_factory=list)


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
    hubs: list[VpnHub] = field(default_factory=list)
    subnets: list[VpnSubnet] = field(default_factory=list)


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
