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
    ContentCategory,
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
    SyslogRole,
    SyslogServer,
    ThreatCategory,
    UplinkState,
    UplinkStatus,
    VlanConfig,
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
    assert {s.value for s in UplinkState} == {"up", "down", "standby", "not_connected"}
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
