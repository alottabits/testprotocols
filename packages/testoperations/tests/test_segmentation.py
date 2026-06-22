"""Tests for testoperations.segmentation (pure role selection + deny construction)."""

from __future__ import annotations

import pytest
from testoperations.segmentation import (
    NoEligibleSelectionError,
    RoleAssignment,
    SpokeCandidate,
    build_deny_rule,
    find_matching_deny,
    select_roles,
)
from testprotocols.models import L3Rule, RuleAction, RuleProtocol

HUB = "SDWAN-MX-AMSTERDAM"


def _spoke(name: str, model: str, hub: str = HUB, subnet: str = "10.1.0.0/24") -> SpokeCandidate:
    return SpokeCandidate(name=name, mx_model=model, hub=hub, subnet=subnet)


# --- select_roles ------------------------------------------------------------


class TestSelectRoles:
    def _three(self) -> list[SpokeCandidate]:
        # Deliberately unsorted input to prove ordering is by name, not arrival.
        return [
            _spoke("Rotterdam", "MX250", subnet="10.1.30.0/24"),
            _spoke("Amsterdam", "MX450", subnet="10.1.41.0/24"),
            _spoke("Ermelo", "MX85", subnet="10.1.40.0/24"),
        ]

    def test_source_selected_by_model(self):
        a = select_roles(self._three(), "MX85")
        assert isinstance(a, RoleAssignment)
        assert a.source.name == "Ermelo"
        assert a.source.mx_model == "MX85"

    def test_destination_and_control_are_the_other_two(self):
        a = select_roles(self._three(), "MX85")
        roles = {a.source.name, a.destination.name, a.control.name}
        assert roles == {"Ermelo", "Amsterdam", "Rotterdam"}
        assert a.destination.name != a.control.name
        assert a.source.name not in (a.destination.name, a.control.name)

    def test_dest_control_deterministic_by_name(self):
        # Source MX85=Ermelo; remaining sorted by name -> Amsterdam, Rotterdam.
        a = select_roles(self._three(), "MX85")
        assert a.destination.name == "Amsterdam"
        assert a.control.name == "Rotterdam"

    def test_repeatable(self):
        a1 = select_roles(self._three(), "MX450")
        a2 = select_roles(self._three(), "MX450")
        assert a1 == a2

    def test_source_is_first_by_name_when_model_duplicated(self):
        cands = [
            _spoke("Zwolle", "MX250"),
            _spoke("Apeldoorn", "MX250"),
            _spoke("Breda", "MX450"),
        ]
        a = select_roles(cands, "MX250")
        assert a.source.name == "Apeldoorn"  # first by name among the MX250s

    def test_raises_when_model_absent(self):
        with pytest.raises(NoEligibleSelectionError, match="MX999"):
            select_roles(self._three(), "MX999")

    def test_raises_when_too_few_same_domain_peers(self):
        # Source's hub has only the source; the others home to a different hub.
        cands = [
            _spoke("Source", "MX85", hub="HUB-A"),
            _spoke("Other1", "MX250", hub="HUB-B"),
            _spoke("Other2", "MX450", hub="HUB-B"),
        ]
        with pytest.raises(NoEligibleSelectionError, match="HUB-A"):
            select_roles(cands, "MX85")

    def test_only_same_domain_peers_are_eligible(self):
        # Two share the source's hub; a third in another domain is ignored.
        cands = [
            _spoke("Amsterdam", "MX450", hub="HUB-A"),
            _spoke("Rotterdam", "MX250", hub="HUB-A"),
            _spoke("Ermelo", "MX85", hub="HUB-A"),
            _spoke("Foreign", "MX250", hub="HUB-B"),
        ]
        a = select_roles(cands, "MX450")
        assert {a.destination.name, a.control.name} == {"Ermelo", "Rotterdam"}


# --- build_deny_rule ---------------------------------------------------------

_ARGS = {
    "source_subnet": "10.1.40.0/24",
    "source_host": "10.1.40.50",
    "dest_subnet": "10.1.41.0/24",
    "dest_host": "10.1.41.50",
}


class TestBuildDenyRule:
    def test_host_scope_uses_slash32_hosts(self):
        r = build_deny_rule(scope="host", proto="icmp", **_ARGS)
        assert r.src_cidr == "10.1.40.50/32"
        assert r.dst_cidr == "10.1.41.50/32"

    def test_subnet_scope_uses_subnets(self):
        r = build_deny_rule(scope="subnet", proto="any", **_ARGS)
        assert r.src_cidr == "10.1.40.0/24"
        assert r.dst_cidr == "10.1.41.0/24"

    def test_action_is_deny_and_syslog_on_by_default(self):
        r = build_deny_rule(scope="host", proto="icmp", **_ARGS)
        assert r.action is RuleAction.DENY
        assert r.syslog_enabled is True

    def test_protocol_maps_from_string(self):
        assert build_deny_rule(scope="host", proto="udp", **_ARGS).protocol is RuleProtocol.UDP
        assert (
            build_deny_rule(scope="subnet", proto="any", **_ARGS).protocol is RuleProtocol.ANY
        )

    def test_comment_passthrough(self):
        r = build_deny_rule(scope="host", proto="tcp", comment="UC-MERAKI-006", **_ARGS)
        assert r.comment == "UC-MERAKI-006"

    def test_unknown_scope_raises(self):
        with pytest.raises(ValueError, match="scope"):
            build_deny_rule(scope="vlan", proto="icmp", **_ARGS)

    def test_invalid_protocol_raises(self):
        with pytest.raises(ValueError):
            build_deny_rule(scope="host", proto="sctp", **_ARGS)


# --- find_matching_deny ------------------------------------------------------


class TestFindMatchingDeny:
    def _rules(self) -> list[L3Rule]:
        return [
            L3Rule(
                action=RuleAction.ALLOW, protocol=RuleProtocol.ANY, src_cidr="any", dst_cidr="any"
            ),
            L3Rule(
                action=RuleAction.DENY,
                protocol=RuleProtocol.ICMP,
                src_cidr="10.1.40.50/32",
                dst_cidr="10.1.41.50/32",
            ),
        ]

    def test_finds_matching_deny(self):
        found = find_matching_deny(
            self._rules(),
            protocol=RuleProtocol.ICMP,
            src_cidr="10.1.40.50/32",
            dst_cidr="10.1.41.50/32",
        )
        assert found is not None
        assert found.action is RuleAction.DENY

    def test_returns_none_when_protocol_differs(self):
        assert (
            find_matching_deny(
                self._rules(),
                protocol=RuleProtocol.TCP,
                src_cidr="10.1.40.50/32",
                dst_cidr="10.1.41.50/32",
            )
            is None
        )

    def test_returns_none_when_cidr_differs(self):
        assert (
            find_matching_deny(
                self._rules(),
                protocol=RuleProtocol.ICMP,
                src_cidr="10.1.40.50/32",
                dst_cidr="10.9.9.9/32",
            )
            is None
        )

    def test_ignores_allow_rule_with_same_tuple(self):
        rules = [
            L3Rule(
                action=RuleAction.ALLOW,
                protocol=RuleProtocol.ICMP,
                src_cidr="10.1.40.50/32",
                dst_cidr="10.1.41.50/32",
            ),
        ]
        assert (
            find_matching_deny(
                rules,
                protocol=RuleProtocol.ICMP,
                src_cidr="10.1.40.50/32",
                dst_cidr="10.1.41.50/32",
            )
            is None
        )
