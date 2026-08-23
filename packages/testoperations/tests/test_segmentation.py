"""Tests for testoperations.segmentation (pure role selection + deny construction)."""

from __future__ import annotations

from typing import TypedDict

import pytest
from testoperations.segmentation import (
    DECOY_RANGE,
    DecoyDerivation,
    NoEligibleSelectionError,
    RoleAssignment,
    SpokeCandidate,
    build_deny_rule,
    derive_decoy_target,
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

    def test_source_selected_by_model(self) -> None:
        a = select_roles(self._three(), "MX85")
        assert isinstance(a, RoleAssignment)
        assert a.source.name == "Ermelo"
        assert a.source.mx_model == "MX85"

    def test_destination_and_control_are_the_other_two(self) -> None:
        a = select_roles(self._three(), "MX85")
        roles = {a.source.name, a.destination.name, a.control.name}
        assert roles == {"Ermelo", "Amsterdam", "Rotterdam"}
        assert a.destination.name != a.control.name
        assert a.source.name not in (a.destination.name, a.control.name)

    def test_dest_control_deterministic_by_name(self) -> None:
        # Source MX85=Ermelo; remaining sorted by name -> Amsterdam, Rotterdam.
        a = select_roles(self._three(), "MX85")
        assert a.destination.name == "Amsterdam"
        assert a.control.name == "Rotterdam"

    def test_repeatable(self) -> None:
        a1 = select_roles(self._three(), "MX450")
        a2 = select_roles(self._three(), "MX450")
        assert a1 == a2

    def test_source_is_first_by_name_when_model_duplicated(self) -> None:
        cands = [
            _spoke("Zwolle", "MX250"),
            _spoke("Apeldoorn", "MX250"),
            _spoke("Breda", "MX450"),
        ]
        a = select_roles(cands, "MX250")
        assert a.source.name == "Apeldoorn"  # first by name among the MX250s

    def test_raises_when_model_absent(self) -> None:
        with pytest.raises(NoEligibleSelectionError, match="MX999"):
            select_roles(self._three(), "MX999")

    def test_raises_when_too_few_same_domain_peers(self) -> None:
        # Source's hub has only the source; the others home to a different hub.
        cands = [
            _spoke("Source", "MX85", hub="HUB-A"),
            _spoke("Other1", "MX250", hub="HUB-B"),
            _spoke("Other2", "MX450", hub="HUB-B"),
        ]
        with pytest.raises(NoEligibleSelectionError, match="HUB-A"):
            select_roles(cands, "MX85")

    def test_only_same_domain_peers_are_eligible(self) -> None:
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


class _Endpoints(TypedDict):
    """The four address arguments every build_deny_rule case shares.

    A TypedDict rather than a plain dict so ``**_ARGS`` keeps its per-key types
    at the call site; a ``dict[str, str]`` would collapse them and collide with
    the keyword-only ``syslog_enabled: bool``.
    """

    source_subnet: str
    source_host: str
    dest_subnet: str
    dest_host: str


_ARGS: _Endpoints = {
    "source_subnet": "10.1.40.0/24",
    "source_host": "10.1.40.50",
    "dest_subnet": "10.1.41.0/24",
    "dest_host": "10.1.41.50",
}


class TestBuildDenyRule:
    def test_host_scope_uses_slash32_hosts(self) -> None:
        r = build_deny_rule(scope="host", proto="icmp", **_ARGS)
        assert r.src_cidr == "10.1.40.50/32"
        assert r.dst_cidr == "10.1.41.50/32"

    def test_subnet_scope_uses_subnets(self) -> None:
        r = build_deny_rule(scope="subnet", proto="any", **_ARGS)
        assert r.src_cidr == "10.1.40.0/24"
        assert r.dst_cidr == "10.1.41.0/24"

    def test_action_is_deny_and_syslog_on_by_default(self) -> None:
        r = build_deny_rule(scope="host", proto="icmp", **_ARGS)
        assert r.action is RuleAction.DENY
        assert r.syslog_enabled is True

    def test_protocol_maps_from_string(self) -> None:
        assert build_deny_rule(scope="host", proto="udp", **_ARGS).protocol is RuleProtocol.UDP
        assert build_deny_rule(scope="subnet", proto="any", **_ARGS).protocol is RuleProtocol.ANY

    def test_comment_passthrough(self) -> None:
        r = build_deny_rule(scope="host", proto="tcp", comment="segmentation-deny", **_ARGS)
        assert r.comment == "segmentation-deny"

    def test_unknown_scope_raises(self) -> None:
        with pytest.raises(ValueError, match="scope"):
            build_deny_rule(scope="vlan", proto="icmp", **_ARGS)

    def test_invalid_protocol_raises(self) -> None:
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

    def test_finds_matching_deny(self) -> None:
        found = find_matching_deny(
            self._rules(),
            protocol=RuleProtocol.ICMP,
            src_cidr="10.1.40.50/32",
            dst_cidr="10.1.41.50/32",
        )
        assert found is not None
        assert found.action is RuleAction.DENY

    def test_returns_none_when_protocol_differs(self) -> None:
        assert (
            find_matching_deny(
                self._rules(),
                protocol=RuleProtocol.TCP,
                src_cidr="10.1.40.50/32",
                dst_cidr="10.1.41.50/32",
            )
            is None
        )

    def test_returns_none_when_cidr_differs(self) -> None:
        assert (
            find_matching_deny(
                self._rules(),
                protocol=RuleProtocol.ICMP,
                src_cidr="10.1.40.50/32",
                dst_cidr="10.9.9.9/32",
            )
            is None
        )

    def test_ignores_allow_rule_with_same_tuple(self) -> None:
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


# --- derive_decoy_target ------------------------------------------------------


def test_decoy_deterministic_with_fixed_forms() -> None:
    first = derive_decoy_target([])
    second = derive_decoy_target([])
    assert first == second
    assert first == DecoyDerivation(subnet="198.51.100.0/24", host="198.51.100.1/32", collisions=())


def test_decoy_clean_on_a_realistic_in_use_set() -> None:
    derivation = derive_decoy_target(
        ["10.1.30.0/24", "10.8.1.0/24", "198.18.200.0/24", "198.18.63.120/29", "192.168.114.0/24"]
    )
    assert derivation.collisions == ()


def test_decoy_supernet_swallowing_the_range_collides() -> None:
    assert derive_decoy_target(["198.51.0.0/16"]).collisions == ("198.51.0.0/16",)


def test_decoy_host_inside_the_range_collides() -> None:
    assert derive_decoy_target(["198.51.100.9/32"]).collisions == ("198.51.100.9/32",)


def test_decoy_exact_range_equality_collides() -> None:
    assert derive_decoy_target([DECOY_RANGE]).collisions == ("198.51.100.0/24",)


def test_decoy_valid_other_family_entries_are_skipped_not_compared() -> None:
    assert derive_decoy_target(["2001:db8::/32", "10.1.30.0/24"]).collisions == ()


def test_decoy_malformed_entry_raises_never_skipped() -> None:
    with pytest.raises(ValueError):
        derive_decoy_target(["not-a-cidr", "10.1.30.0/24"])


def test_decoy_host_bearing_entry_is_normalized_and_still_checked() -> None:
    assert derive_decoy_target(["198.51.100.7/24"]).collisions == ("198.51.100.0/24",)


def test_decoy_collisions_deduplicated_in_input_order() -> None:
    derivation = derive_decoy_target(["198.51.100.0/24", "198.51.100.0/24", "198.51.0.0/16"])
    assert derivation.collisions == ("198.51.100.0/24", "198.51.0.0/16")
