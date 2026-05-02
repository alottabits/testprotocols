"""WAN edge device data models for links, routes, SLA, flows, VPN, and shaping."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
    """Holds the current operational state and IP address of a WAN link."""

    name: str
    state: str  # "up" | "down" | "degraded"
    ip_address: str


@dataclass
class RouteEntry:
    """Holds a single routing table entry with destination, gateway, interface, and metric."""

    destination: str
    gateway: str
    interface: str
    metric: int


@dataclass
class SLAPolicy:
    """Holds SLA thresholds for latency, jitter, and packet loss."""

    name: str
    max_latency_ms: float = 150.0
    max_jitter_ms: float = 30.0
    max_loss_percent: float = 10.0


@dataclass
class LinkHealthReport:
    """Holds a summary of link health including state, routing, metrics, and SLA compliance."""

    state: str
    route_installed: bool
    avg_rtt_ms: float | None
    jitter_ms: float | None
    loss_percent: float
    sla_compliant: bool
    mos: float | None = None


@dataclass
class AppFlow:
    """Holds per-application flow data observed on a WAN interface."""

    application: str
    category: str
    src_ip: str
    dst_ip: str
    wan_interface: str
    bytes_sent: int
    bytes_received: int


@dataclass
class VPNPeerStatus:
    """Holds the reachability and uplink state of a VPN peer."""

    peer_id: str
    peer_name: str
    reachability: str
    uplink: str


@dataclass
class TrafficShapingRule:
    """Holds a traffic shaping rule.

    Includes match criteria and optional DSCP, bandwidth, or priority.
    """

    name: str
    match: dict[str, Any]
    dscp_tag: int | None = None
    bandwidth_limit_kbps: int | None = None
    priority: str | None = None
