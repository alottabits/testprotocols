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
    """Operational state of a WAN uplink."""

    UP = "up"
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
