"""Tests for the SD-WAN appliance data models + their normalized vocabularies.

The value vocabularies are ``StrEnum``s: members *are* strings (clean JSON/REST
serialization), construction validates an incoming value (runtime safety at the
vendor-ingest boundary), and they give static checking at driver/test call sites.
"""

from __future__ import annotations

from enum import StrEnum

import pytest

from testprotocols.models.sdwan_appliance import (
    ApplicationCategory,
    BgpConfig,
    BgpNeighbor,
    BgpPeerStatus,
    BgpSessionState,
    ContentCategory,
    FlowMatch,
    L3Rule,
    L7MatchType,
    L7Rule,
    RuleAction,
    RuleProtocol,
    DhcpLease,
    DhcpMode,
    DhcpOption,
    DhcpOptionType,
    IntrusionConfig,
    IntrusionMode,
    IntrusionSensitivity,
    MalwareMode,
    SecurityAction,
    SecurityEvent,
    ShapingPriority,
    ShapingRule,
    SiteToSiteVpnConfig,
    StaticRoute,
    SteeringScope,
    SyslogRole,
    SyslogServer,
    ThreatCategory,
    UplinkSelectionRule,
    UplinkState,
    UplinkStatus,
    VlanConfig,
    VpnHub,
    VpnPeerState,
    VpnPeerStatus,
    VpnRole,
    VpnSubnet,
)


def test_normalized_vocabularies_are_strenums() -> None:
    assert issubclass(RuleAction, StrEnum)
    assert issubclass(RuleProtocol, StrEnum)


def test_members_are_strings_for_clean_serialization() -> None:
    assert RuleAction.ALLOW == "allow"
    assert isinstance(RuleAction.DENY, str)
    assert RuleProtocol.ICMP6 == "icmp6"


def test_construction_validates_at_the_boundary() -> None:
    # a driver narrows a vendor value with RuleAction(value); a bad value raises
    assert RuleAction("deny") is RuleAction.DENY
    with pytest.raises(ValueError):
        RuleAction("permit")


def test_rule_protocol_vocabulary() -> None:
    assert {p.value for p in RuleProtocol} == {"tcp", "udp", "icmp", "icmp6", "any"}


def test_l3rule_uses_the_normalized_vocabulary() -> None:
    rule = L3Rule(action=RuleAction.DENY, protocol=RuleProtocol.TCP, dst_cidr="1.1.1.1/32")
    assert rule.action == "deny"
    assert rule.protocol == "tcp"
    assert L3Rule(action=RuleAction.ALLOW).protocol is RuleProtocol.ANY


def test_content_category_is_a_normalized_strenum_taxonomy() -> None:
    assert issubclass(ContentCategory, StrEnum)
    assert ContentCategory.GAMBLING == "gambling"
    assert ContentCategory.SPORTS == "sports"
    # a fuller standard set is seeded (not just the evidenced two)
    assert len(ContentCategory) >= 20
    with pytest.raises(ValueError):
        ContentCategory("not_a_category")


def test_application_category_is_a_normalized_strenum_taxonomy() -> None:
    assert issubclass(ApplicationCategory, StrEnum)
    assert ApplicationCategory.VIDEO_STREAMING == "video_streaming"
    # evidence-driven member: L7 block-by-app-category acceptance test (sports)
    assert ApplicationCategory.SPORTS == "sports"
    assert len(ApplicationCategory) >= 15
    with pytest.raises(ValueError):
        ApplicationCategory("not_a_category")


def test_l7_match_type_and_rule() -> None:
    assert issubclass(L7MatchType, StrEnum)
    rule = L7Rule(
        action=RuleAction.DENY,
        match_type=L7MatchType.APPLICATION_CATEGORY,
        value=ApplicationCategory.SOCIAL_NETWORKING,
    )
    assert rule.action == "deny"
    assert rule.match_type == "application_category"
    assert rule.value == "social_networking"


def test_shaping_rule_uses_normalized_vocabulary() -> None:
    assert issubclass(ShapingPriority, StrEnum)
    rule = ShapingRule(
        name="cap-video",
        match_type=L7MatchType.APPLICATION_CATEGORY,
        value=ApplicationCategory.VIDEO_STREAMING,
        bandwidth_limit_kbps=5000,
        dscp_tag=34,
        priority=ShapingPriority.LOW,
    )
    assert rule.priority == "low"
    assert ShapingRule(name="x", match_type=L7MatchType.HOST, value="1.2.3.4").priority is ShapingPriority.NORMAL


def test_uplink_state_and_status() -> None:
    assert issubclass(UplinkState, StrEnum)
    assert {s.value for s in UplinkState} == {"up", "degraded", "down", "standby", "not_connected"}
    up = UplinkStatus(name="wan1", state=UplinkState.UP, ip="203.0.113.5")
    assert up.state == "up"


def test_syslog_role_and_server() -> None:
    assert issubclass(SyslogRole, StrEnum)
    srv = SyslogServer(host="10.0.0.1", roles=[SyslogRole.EVENT_LOG, SyslogRole.SECURITY])
    assert srv.port == 514
    assert SyslogRole.FLOWS in {r for r in SyslogRole}


def test_threat_prevention_vocabularies() -> None:
    for enum_cls in (IntrusionMode, IntrusionSensitivity, MalwareMode, SecurityAction, ThreatCategory):
        assert issubclass(enum_cls, StrEnum)
    assert {m.value for m in IntrusionMode} == {"disabled", "detection", "prevention"}
    assert {s.value for s in IntrusionSensitivity} == {"low", "medium", "high"}
    cfg = IntrusionConfig(mode=IntrusionMode.PREVENTION, sensitivity=IntrusionSensitivity.HIGH)
    assert cfg.mode == "prevention"
    evt = SecurityEvent(
        ts="2026-06-11T10:00:00Z",
        src_ip="10.0.0.5",
        dst_ip="1.2.3.4",
        protocol=RuleProtocol.TCP,
        action=SecurityAction.BLOCKED,
        category=ThreatCategory.MALWARE,
    )
    assert evt.action == "blocked"
    assert evt.category == "malware"


def test_vlan_and_dhcp_models() -> None:
    assert issubclass(DhcpMode, StrEnum)
    assert issubclass(DhcpOptionType, StrEnum)
    vlan = VlanConfig(
        vlan_id=100,
        name="data",
        subnet="10.0.100.0/24",
        appliance_ip="10.0.100.1",
        dhcp_options=[DhcpOption(code=42, type=DhcpOptionType.IP, value="10.0.100.2")],
    )
    assert vlan.dhcp_mode is DhcpMode.SERVER  # default
    assert vlan.dhcp_lease_seconds == 86400
    lease = DhcpLease(mac="00:11:22:33:44:55", ip="10.0.100.50", hostname="host1", vlan_id=100)
    assert lease.ip == "10.0.100.50"


def test_vpn_vocabularies_are_normalized_strenums() -> None:
    assert issubclass(VpnRole, StrEnum)
    assert issubclass(VpnPeerState, StrEnum)
    # members are strings; construction validates at the vendor-ingest boundary
    assert VpnRole.SPOKE == "spoke"
    assert VpnRole("hub") is VpnRole.HUB
    assert VpnPeerState.REACHABLE == "reachable"
    with pytest.raises(ValueError):
        VpnRole("mesh")  # not seeded — grows on evidence
    with pytest.raises(ValueError):
        VpnPeerState("degraded")


def test_site_to_site_vpn_config_models() -> None:
    hub = VpnHub(name="hub-1")
    assert hub.use_default_route is False
    subnet = VpnSubnet(subnet="192.168.10.0/24")
    assert subnet.advertise is True
    config = SiteToSiteVpnConfig(role=VpnRole.SPOKE, hubs=[hub], subnets=[subnet])
    assert config.role is VpnRole.SPOKE
    assert config.hubs[0].name == "hub-1"
    # role-only construction: hubs/subnets default to empty, instances independent
    a = SiteToSiteVpnConfig(role=VpnRole.DISABLED)
    b = SiteToSiteVpnConfig(role=VpnRole.HUB)
    a.hubs.append(hub)
    assert b.hubs == []


def test_vpn_peer_status_model() -> None:
    peer = VpnPeerStatus(name="hub-1", state=VpnPeerState.REACHABLE)
    assert peer.uplink == ""
    assert peer.state == "reachable"  # StrEnum: serializes as the plain string


def test_steering_scope_and_flow_match() -> None:
    assert issubclass(SteeringScope, StrEnum)
    assert SteeringScope("internet") is SteeringScope.INTERNET
    assert SteeringScope.OVERLAY == "overlay"
    with pytest.raises(ValueError):
        SteeringScope("any")  # deliberately not seeded — intent must be explicit
    m = FlowMatch()
    assert (m.protocol, m.src_cidr, m.src_port, m.dst_cidr, m.dst_port) == (
        RuleProtocol.ANY,
        "any",
        "any",
        "any",
        "any",
    )


def test_uplink_selection_rule_defaults() -> None:
    rule = UplinkSelectionRule(
        name="steer-dns",
        scope=SteeringScope.INTERNET,
        match=FlowMatch(dst_cidr="198.51.100.4/32"),
        preferred_uplink="wan2",
    )
    assert rule.performance_class is None
    assert rule.match.dst_cidr == "198.51.100.4/32"
    assert rule.scope == "internet"  # StrEnum: serializes as the plain string


def test_static_route_model() -> None:
    route = StaticRoute(
        name="to-lan", destination_cidr="172.16.5.0/24", next_hop="10.0.100.2"
    )
    assert (route.name, route.destination_cidr, route.next_hop) == (
        "to-lan",
        "172.16.5.0/24",
        "10.0.100.2",
    )


def test_bgp_session_state_is_the_rfc_fsm_vocabulary() -> None:
    assert issubclass(BgpSessionState, StrEnum)
    assert {s.value for s in BgpSessionState} == {
        "idle",
        "connect",
        "active",
        "open_sent",
        "open_confirm",
        "established",
        "unknown",
    }
    assert BgpSessionState("established") is BgpSessionState.ESTABLISHED
    with pytest.raises(ValueError):
        BgpSessionState("flapping")


def test_bgp_config_models() -> None:
    neighbor = BgpNeighbor(peer_ip="192.168.10.20", remote_as=65010)
    config = BgpConfig(enabled=True, as_number=65000, neighbors=[neighbor])
    assert config.advertised_networks == []
    assert config.neighbors[0].remote_as == 65010
    # default factories: instances independent
    a = BgpConfig(enabled=False, as_number=1)
    b = BgpConfig(enabled=False, as_number=2)
    a.neighbors.append(neighbor)
    assert b.neighbors == []


def test_bgp_peer_status_model() -> None:
    peer = BgpPeerStatus(
        peer_ip="192.168.10.20", remote_as=65010, state=BgpSessionState.ESTABLISHED
    )
    assert peer.prefixes_received is None
    assert peer.state == "established"
