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
