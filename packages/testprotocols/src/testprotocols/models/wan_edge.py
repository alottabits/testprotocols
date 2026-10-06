"""WAN edge device data models for links, routes, SLA, flows, VPN, and shaping."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from testprotocols._compat import deprecated
from testprotocols.models.sdwan_appliance import UplinkState


@dataclass
class PathMetrics:
    """Holds measured path quality metrics for a WAN link."""

    latency_ms: float
    jitter_ms: float
    loss_percent: float
    link_name: str
    mos: float | None = None


@dataclass
class LinkStatus:
    """Holds the current operational state and IP address of a WAN link.

    *state* is an :class:`~testprotocols.models.UplinkState`; every member is
    accepted (``up``, ``down`` and ``degraded`` are the common ones). A plain
    ``str`` naming one is accepted and stored as given. ``ip_address`` is ``""`` when the
    link has none.

    Deprecated: the plain ``str`` form of *state*; the field narrows to
    :class:`~testprotocols.models.UplinkState`. Deprecated: ``""`` as "no address" in
    *ip_address*; the field becomes ``str | None``, and ``""`` means none until then.
    Removal not before the first release 6 months after the release that deprecates each.
    """

    name: str
    state: UplinkState | str
    ip_address: str


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

    *uptime_seconds* is the time since the device started, or ``None`` when the device
    reports no uptime (a cloud-managed appliance's management API may not; see
    ``GAPS.md``, 2026-06-11, "appliance health / online capability", whose recorded shape
    for an uptime read is ``float | None``). It is required: a driver states ``None``
    rather than leaving it out. *cpu_load_percent* and *mem_used_percent* are ``None``
    when the device does not report them. Each value given is finite and not negative.
    Returned by ``Router.read_telemetry``.
    """

    uptime_seconds: float | None
    cpu_load_percent: float | None = None
    mem_used_percent: float | None = None


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
    link. A plain ``str`` naming one is accepted and stored as given.

    Deprecated: the plain ``str`` form of *state*; the field narrows to
    :class:`~testprotocols.models.UplinkState`. Removal not before the first release 6
    months after the release that deprecates it.
    """

    state: UplinkState | str
    route_installed: bool
    avg_rtt_ms: float | None
    jitter_ms: float | None
    loss_percent: float
    sla_compliant: bool
    mos: float | None = None


@dataclass
class AppFlow:
    """Holds per-application flow data observed on a WAN interface.

    *category* is the product's own word, stored as given; the common ones are the
    values of :class:`~testprotocols.models.ApplicationCategory`.
    """

    application: str
    category: str
    src_ip: str
    dst_ip: str
    wan_interface: str
    bytes_sent: int
    bytes_received: int


@deprecated(
    "Deprecated, with no successor. Removal not before the first release 6 months after "
    "the release that deprecates it.",
    category=None,
)
@dataclass
class VPNPeerStatus:
    """Holds the reachability and uplink state of a VPN peer.

    No capability returns it. The site-to-site VPN capability reports
    ``testprotocols.models.VpnPeerStatus``.

    Deprecated, with no successor. Removal not before the first release 6 months after the
    release that deprecates it.
    """

    peer_id: str
    peer_name: str
    reachability: str
    uplink: str


@deprecated(
    "Deprecated, with no successor. Removal not before the first release 6 months after "
    "the release that deprecates it.",
    category=None,
)
@dataclass
class TrafficShapingRule:
    """Holds a traffic shaping rule.

    Includes match criteria and optional DSCP, bandwidth, or priority.

    No capability takes or returns it. Traffic shaping uses
    ``testprotocols.models.ShapingRule``.

    Deprecated, with no successor. Removal not before the first release 6 months after the
    release that deprecates it.
    """

    name: str
    match: Mapping[str, object]  # object: deprecated form kept until removal
    dscp_tag: int | None = None
    bandwidth_limit_kbps: int | None = None
    priority: str | None = None
