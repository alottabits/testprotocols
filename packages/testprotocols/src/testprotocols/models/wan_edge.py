"""WAN edge device data models for links, routes, SLA, flows, VPN, and shaping."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, cast, override

from testprotocols.deprecation import MODEL_FRAMES, coerce_enum, deprecated_attribute
from testprotocols.models.sdwan_appliance import UplinkState


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

    *state* is an :class:`~testprotocols.models.UplinkState`; every member is
    accepted (``up``, ``down`` and ``degraded`` are the common ones). A plain
    ``str`` naming one is deprecated: it warns and is converted, also on
    assignment, so a reader always holds the enum; any other string raises ``ValueError``.
    ``ip_address`` is ``""`` when the link has none; it will become
    ``str | None``, and ``""`` means none until then.
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
    ``TypeError``) and finite and not negative (``ValueError``; ``nan`` and
    ``inf`` are refused). Returned by ``Router.read_telemetry``; :meth:`as_dict` is the released
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
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"Telemetry.{name} must be finite and not negative, got {value}")

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
    # warns; type checkers still see the definitions above. ``__getattr__`` is defined
    # here too, not at module level: a checker that saw it would type every unknown
    # name as ``object``.
    del VPNPeerStatus, TrafficShapingRule

    def __getattr__(name: str) -> object:
        return deprecated_attribute(__name__, name, ORPHAN_REASON, DEPRECATED_ORPHANS)
