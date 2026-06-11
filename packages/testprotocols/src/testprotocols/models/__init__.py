"""Shared data models for palco-templates."""

from __future__ import annotations

from testprotocols.models.dhcp import DHCPTraceData, DHCPV6TraceData
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
from testprotocols.models.sdwan_appliance import (
    ApplicationCategory,
    ContentCategory,
    L3Rule,
    L7MatchType,
    L7Rule,
    NatInboundAllow,
    OneToManyNatRule,
    OneToOneNatRule,
    PortForwardRule,
    RuleAction,
    RuleProtocol,
    ShapingPriority,
    ShapingRule,
    SyslogRole,
    SyslogServer,
    UplinkState,
    UplinkStatus,
)
from testprotocols.models.radius import (
    RadiusAccountingRecord,
    RadiusServerConfig,
    RadiusSession,
    RadiusUser,
)
from testprotocols.models.tr069 import CpeConnectionStatus
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
    # wan_edge
    "AppFlow",
    # firewall
    "Connection",
    "ConntrackStats",
    # tr069
    "CpeConnectionStatus",
    # dhcp
    "DHCPTraceData",
    "DHCPV6TraceData",
    "FirewallRule",
    # networking
    "HTTPResult",
    "ICMPPacketData",
    "IPAddresses",
    # impairment
    "ImpairmentProfile",
    # sdwan_appliance
    "ApplicationCategory",
    "ContentCategory",
    "L3Rule",
    "L7MatchType",
    "L7Rule",
    "NatInboundAllow",
    "OneToManyNatRule",
    "OneToOneNatRule",
    "PortForwardRule",
    "RuleAction",
    "RuleProtocol",
    "ShapingPriority",
    "ShapingRule",
    "SyslogRole",
    "SyslogServer",
    "UplinkState",
    "UplinkStatus",
    "LinkHealthReport",
    "LinkStatus",
    # multicast
    "McastGroup",
    "McastSource",
    # qoe
    "MeasurementSpec",
    "MulticastGroupRecord",
    "MulticastGroupRecordType",
    "NatRule",
    "PathMetrics",
    "PortMapping",
    "QoEResult",
    # packets
    "RIPv2PacketData",
    # radius
    "RadiusAccountingRecord",
    "RadiusServerConfig",
    "RadiusSession",
    "RadiusUser",
    "RouteEntry",
    "SLAPolicy",
    # traffic
    "TrafficResult",
    "TrafficShapingRule",
    "TrafficSpec",
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
    "Zone",
    "ZonePolicy",
]
