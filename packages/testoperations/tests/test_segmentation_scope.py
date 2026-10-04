"""build_deny_rule takes DenyScope and RuleProtocol (shape 1)."""

from __future__ import annotations

import warnings
from typing import TypedDict

import pytest
from testoperations.segmentation import DenyScope, build_deny_rule
from testprotocols.models import RuleProtocol


class _Endpoints(TypedDict):
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


def test_deny_scope_is_a_str_enum_of_host_and_subnet() -> None:
    assert [m.value for m in DenyScope] == ["host", "subnet"]
    assert str(DenyScope.HOST) == "host"
    assert DenyScope("subnet") is DenyScope.SUBNET


def test_members_build_the_rule_silently() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        host = build_deny_rule(scope=DenyScope.HOST, proto=RuleProtocol.TCP, **_ARGS)
        net = build_deny_rule(scope=DenyScope.SUBNET, proto=RuleProtocol.ANY, **_ARGS)
    assert (host.src_cidr, host.dst_cidr) == ("10.1.40.50/32", "10.1.41.50/32")
    assert host.protocol is RuleProtocol.TCP
    assert (net.src_cidr, net.dst_cidr) == ("10.1.40.0/24", "10.1.41.0/24")


def test_plain_strings_warn_and_still_work() -> None:
    with pytest.warns(DeprecationWarning, match=r"scope: plain string 'host'") as scope_warning:
        r = build_deny_rule(scope="host", proto=RuleProtocol.UDP, **_ARGS)
    assert r.src_cidr == "10.1.40.50/32"
    assert scope_warning[0].filename == __file__
    with pytest.warns(DeprecationWarning, match=r"proto: plain string 'icmp'") as proto_warning:
        r = build_deny_rule(scope=DenyScope.SUBNET, proto="icmp", **_ARGS)
    assert r.protocol is RuleProtocol.ICMP
    assert proto_warning[0].filename == __file__


def test_unknown_words_raise_before_any_rule_is_built() -> None:
    with pytest.raises(ValueError, match="scope"):
        build_deny_rule(scope="vlan", proto=RuleProtocol.ICMP, **_ARGS)
    with pytest.raises(ValueError, match="proto"):
        build_deny_rule(scope=DenyScope.HOST, proto="sctp", **_ARGS)
