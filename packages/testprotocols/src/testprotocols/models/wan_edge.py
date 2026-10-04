"""WAN edge device data models for links, routes, SLA, flows, VPN, and shaping."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, cast, override

from testprotocols.deprecation import MODEL_FRAMES, coerce_enum, deprecated_attribute
from testprotocols.models._open_enum import OpenEnumPair
from testprotocols.models._sync import assign, settle
from testprotocols.models.sdwan_appliance import ApplicationCategory, UplinkState


@dataclass
class PathMetrics:
    """Holds measured path quality metrics for a WAN link."""

    latency_ms: float
    jitter_ms: float
    loss_percent: float
    link_name: str
    mos: float | None = None


def _link_state(owner: str, name: str, value: object) -> UplinkState:
    return coerce_enum(
        UplinkState,
        cast("UplinkState | str", value),
        what=f"{owner}.{name}",
        skip_file_prefixes=MODEL_FRAMES,
    )


@dataclass
class LinkStatus:
    """Holds the current operational state and IP address of a WAN link.

    *state* is an :class:`~testprotocols.models.UplinkState` (``up``, ``down`` or
    ``degraded`` here). A plain ``str`` naming one is deprecated: it warns and is
    converted, also on assignment, so a reader always holds the enum; any other
    string raises ``ValueError``. ``ip_address`` is ``""`` when the link has none;
    it will become ``str | None``, ``""`` means none until then.
    """

    name: str
    state: UplinkState | str
    ip_address: str

    @override
    def __setattr__(self, name: str, value: object) -> None:
        if name == "state":
            value = _link_state("LinkStatus", name, value)
        object.__setattr__(self, name, value)


class RouteOrigin(StrEnum):
    """How a route was learned. Seeded with the standardized origins; ``ISIS`` /
    ``RIP`` grow on evidence (see GAPS.md). ``UNKNOWN`` is the back-compat default
    for callers that do not classify the route."""

    UNKNOWN = "unknown"
    STATIC = "static"
    CONNECTED = "connected"
    OSPF = "ospf"
    BGP = "bgp"
    LOCAL = "local"


@dataclass(frozen=True)
class Telemetry:
    """A device's resource telemetry: uptime, CPU load and memory use.

    *uptime_seconds* is the time since the device started. *cpu_load_percent*
    and *mem_used_percent* are ``None`` when the device does not report them.
    Each is an ``int`` or ``float`` (a ``bool`` or other type raises
    ``TypeError``) and not negative (``ValueError``). Returned by
    ``Router.read_telemetry``; :meth:`as_dict` is the released
    ``Router.get_telemetry`` mapping, so a driver's old member can delegate.
    """

    uptime_seconds: float
    cpu_load_percent: float | None = None
    mem_used_percent: float | None = None

    def __post_init__(self) -> None:
        for name in ("uptime_seconds", "cpu_load_percent", "mem_used_percent"):
            value: object = getattr(self, name)
            if value is None and name != "uptime_seconds":
                continue
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise TypeError(f"Telemetry.{name} must be a number, not {value!r}")
            if value < 0:
                raise ValueError(f"Telemetry.{name} must not be negative, got {value}")

    def as_dict(self) -> dict[str, float]:
        """The released ``get_telemetry`` mapping: the values the device reported,
        keyed by field name (a ``None`` field is absent)."""
        values = {
            "uptime_seconds": self.uptime_seconds,
            "cpu_load_percent": self.cpu_load_percent,
            "mem_used_percent": self.mem_used_percent,
        }
        return {name: value for name, value in values.items() if value is not None}


@dataclass
class RouteEntry:
    """A single routing-table entry: destination, gateway, interface, metric, origin.

    ``origin`` is default-backed so the WAN-edge ``Router.get_routing_table`` and
    ``Bgp.get_learned_routes`` producers stay source-compatible; the switch
    ``RoutingRead`` populates it. See SPLITS.md.
    """

    destination: str
    gateway: str
    interface: str
    metric: int
    origin: RouteOrigin = RouteOrigin.UNKNOWN


@dataclass
class SLAPolicy:
    """Holds SLA thresholds for latency, jitter, and packet loss."""

    name: str
    max_latency_ms: float = 150.0
    max_jitter_ms: float = 30.0
    max_loss_percent: float = 10.0


@dataclass
class LinkHealthReport:
    """Holds a summary of link health including state, routing, metrics, and SLA compliance.

    *state* is an :class:`~testprotocols.models.UplinkState`: ``up``, ``down``,
    ``degraded``, or ``unknown`` when the product has no health data for the
    link. A plain ``str`` naming one is deprecated: it warns and is converted,
    also on assignment, so a reader always holds the enum; any other string raises
    ``ValueError``.
    """

    state: UplinkState | str
    route_installed: bool
    avg_rtt_ms: float | None
    jitter_ms: float | None
    loss_percent: float
    sla_compliant: bool
    mos: float | None = None

    @override
    def __setattr__(self, name: str, value: object) -> None:
        if name == "state":
            value = _link_state("LinkHealthReport", name, value)
        object.__setattr__(self, name, value)


_FLOW_PAIRS = (
    OpenEnumPair(ApplicationCategory, ApplicationCategory.OTHER, "category", "category_raw"),
)


@dataclass
class AppFlow:
    """Holds per-application flow data observed on a WAN interface.

    *category* is an :class:`~testprotocols.models.ApplicationCategory`. The set is
    open: a product may classify traffic into a category the enum does not list, so
    an unknown string is not an error, it becomes ``ApplicationCategory.OTHER`` with
    the product's own word kept in *category_raw* (verbatim, with no warning). A
    plain ``str`` naming a member is deprecated: it warns and is converted.
    *category_raw* is ``None`` unless *category* is ``OTHER``; the pair agrees after
    construction, ``replace`` and assignment, and the side that changed wins (the
    rule of ``Connection.state``): a member clears the raw word, an unknown string
    sets it, a raw word beside a named category raises ``ValueError``.
    """

    application: str
    category: ApplicationCategory | str
    src_ip: str
    dst_ip: str
    wan_interface: str
    bytes_sent: int
    bytes_received: int
    category_raw: str | None = None
    _category_seen: tuple[tuple[ApplicationCategory, str | None], ...] | None = field(
        default=None, kw_only=True, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        settle(self, _FLOW_PAIRS, "_category_seen")

    @override
    def __setattr__(self, name: str, value: object) -> None:
        assign(self, name, value, _FLOW_PAIRS, "_category_seen")


@dataclass
class VPNPeerStatus:
    """Holds the reachability and uplink state of a VPN peer.

    Deprecated, with no successor: no capability returns it. The site-to-site VPN
    capability reports ``testprotocols.models.VpnPeerStatus``.
    """

    peer_id: str
    peer_name: str
    reachability: str
    uplink: str


@dataclass
class TrafficShapingRule:
    """Holds a traffic shaping rule.

    Includes match criteria and optional DSCP, bandwidth, or priority.

    Deprecated, with no successor: no capability takes or returns it. Traffic
    shaping uses ``testprotocols.models.ShapingRule``.
    """

    name: str
    match: Mapping[str, object]
    dscp_tag: int | None = None
    bandwidth_limit_kbps: int | None = None
    priority: str | None = None


# The deprecated orphan models and the reason, shared with ``testprotocols.models``.
ORPHAN_REASON = "no capability uses it and it has no successor; it will be removed"
DEPRECATED_ORPHANS: dict[str, object] = {
    "VPNPeerStatus": VPNPeerStatus,
    "TrafficShapingRule": TrafficShapingRule,
}

if not TYPE_CHECKING:
    # Remove the names at run time so that every access reaches ``__getattr__`` and
    # warns; type checkers still see the definitions above.
    del VPNPeerStatus, TrafficShapingRule


def __getattr__(name: str) -> object:
    return deprecated_attribute(__name__, name, ORPHAN_REASON, DEPRECATED_ORPHANS)
