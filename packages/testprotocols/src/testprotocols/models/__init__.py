"""Shared data models for palco-templates."""
from __future__ import annotations

from testprotocols.models.dhcp import DHCPV6TraceData, DHCPTraceData
from testprotocols.models.firewall import (
    Connection,
    ConntrackStats,
    FirewallRule,
    NatRule,
    PortMapping,
    Zone,
    ZonePolicy,
)
from testprotocols.models.impairment import ImpairmentProfile
from testprotocols.models.multicast import (
    McastGroup,
    McastSource,
    MulticastGroupRecord,
    MulticastGroupRecordType,
)
from testprotocols.models.networking import HTTPResult, ICMPPacketData, IPAddresses
from testprotocols.models.packets import RIPv2PacketData
from testprotocols.models.qoe import MeasurementSpec, QoEResult
from testprotocols.models.radius import (
    RadiusAccountingRecord,
    RadiusServerConfig,
    RadiusSession,
    RadiusUser,
)
from testprotocols.models.traffic import TrafficResult, TrafficSpec
from testprotocols.models.wan_edge import (
    AppFlow,
    LinkHealthReport,
    LinkStatus,
    PathMetrics,
    RouteEntry,
    SLAPolicy,
    TrafficShapingRule,
    VPNPeerStatus,
)
from testprotocols.models.wifi import (
    WifiAcl,
    WifiBssConfig,
    WifiCaptiveConfig,
    WifiChannelUtilization,
    WifiDfsState,
    WifiMeshLink,
    WifiMeshNode,
    WifiMeshStatus,
    WifiMeshTopology,
    WifiNeighbor,
    WifiRadioStats,
    WifiStation,
    WifiTransitionConfig,
)

__all__ = [
    # dhcp
    "DHCPTraceData",
    "DHCPV6TraceData",
    # firewall
    "Connection",
    "ConntrackStats",
    "FirewallRule",
    "NatRule",
    "PortMapping",
    "Zone",
    "ZonePolicy",
    # impairment
    "ImpairmentProfile",
    # multicast
    "McastGroup",
    "McastSource",
    "MulticastGroupRecord",
    "MulticastGroupRecordType",
    # networking
    "HTTPResult",
    "ICMPPacketData",
    "IPAddresses",
    # packets
    "RIPv2PacketData",
    # qoe
    "MeasurementSpec",
    "QoEResult",
    # radius
    "RadiusAccountingRecord",
    "RadiusServerConfig",
    "RadiusSession",
    "RadiusUser",
    # traffic
    "TrafficResult",
    "TrafficSpec",
    # wan_edge
    "AppFlow",
    "LinkHealthReport",
    "LinkStatus",
    "PathMetrics",
    "RouteEntry",
    "SLAPolicy",
    "TrafficShapingRule",
    "VPNPeerStatus",
    # wifi
    "WifiAcl",
    "WifiBssConfig",
    "WifiCaptiveConfig",
    "WifiChannelUtilization",
    "WifiDfsState",
    "WifiMeshLink",
    "WifiMeshNode",
    "WifiMeshStatus",
    "WifiMeshTopology",
    "WifiNeighbor",
    "WifiRadioStats",
    "WifiStation",
    "WifiTransitionConfig",
]
