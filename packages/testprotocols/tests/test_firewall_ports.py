"""FirewallRule and NatRule ports: the released text and the PortRange tuple; RuleCounters."""

from __future__ import annotations

import dataclasses
import typing

import pytest
from testprotocols.models import (
    Chain,
    FirewallRule,
    FirewallRuleAction,
    NatMode,
    NatRule,
    PortRange,
    RuleCounters,
    RuleProtocol,
)
from testprotocols.nat import Nat
from testprotocols.packet_filter import PacketFilter

pytestmark = pytest.mark.filterwarnings("error::DeprecationWarning")


def _rule(**kw: object) -> FirewallRule:
    base: dict[str, object] = {
        "name": "r",
        "action": FirewallRuleAction.ALLOW,
        "protocol": RuleProtocol.TCP,
        "src_cidr": "any",
        "dst_cidr": "any",
        "dst_port": None,
    }
    return FirewallRule(**{**base, **kw})  # type: ignore[arg-type]  # the keyword values are `object`


def _nat(**kw: object) -> NatRule:
    return NatRule(**{"name": "n", "mode": NatMode.DNAT, "interface": "wan", **kw})  # type: ignore[arg-type]  # the keyword values are `object`


# --- FirewallRule ---


def test_each_port_form_is_stored_as_given() -> None:
    ports = (PortRange(80, 90), PortRange.single(22))
    assert (_rule(dst_ports=ports).dst_port, _rule(dst_ports=ports).dst_ports) == (None, ports)
    assert (_rule(dst_port="22, 80-90").dst_port, _rule(dst_port="80").dst_ports) == (
        "22, 80-90",
        None,
    )
    both = _rule(dst_port="80-90,22", dst_ports=ports)
    assert (both.dst_port, both.dst_ports) == ("80-90,22", ports)


def test_released_positional_construction_still_works() -> None:
    r = FirewallRule("r", FirewallRuleAction.ALLOW, RuleProtocol.TCP, "any", "any", "443")
    assert (r.dst_port, r.dst_ports) == ("443", None)


def test_replace_and_assignment_change_one_field_only() -> None:
    r = _rule(dst_ports=(PortRange.single(80),))
    assert dataclasses.replace(r, dst_port="443").dst_ports == (PortRange.single(80),)
    r.dst_ports = (PortRange(1, 2),)
    assert r.dst_port is None


# --- NatRule ---


def test_nat_ports_default_to_the_released_text() -> None:
    n = _nat()
    assert (n.dst_port, n.translated_port, n.dst_ports, n.translated_ports) == (
        "",
        "",
        None,
        None,
    )


def test_nat_port_forms_are_stored_as_given() -> None:
    n = _nat(dst_ports=(PortRange.single(8080),), translated_port="80")
    assert (n.dst_port, n.dst_ports) == ("", (PortRange.single(8080),))
    assert (n.translated_port, n.translated_ports) == ("80", None)
    assert _nat(dst_port="", translated_port="").dst_port == ""


# --- RuleCounters ---


def test_rule_counters_hold_values_and_are_frozen() -> None:
    c = RuleCounters(packets=3, bytes=4)
    assert (c.packets, c.bytes) == (3, 4)
    assert RuleCounters(0, 0) == RuleCounters(0, 0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        c.packets = 1  # type: ignore[misc]  # assigning a frozen field is the check


def test_new_counter_members_exist_and_old_remain() -> None:
    assert callable(PacketFilter.get_rule_counter_values)
    assert callable(PacketFilter.get_rule_counters)  # type: ignore[deprecated]  # the released member under test
    assert callable(Nat.get_nat_rule_counter_values)
    assert callable(Nat.get_nat_rule_counters)  # type: ignore[deprecated]  # the released member under test


def test_counter_values_member_takes_the_bare_chain() -> None:
    hints = typing.get_type_hints(PacketFilter.get_rule_counter_values)
    assert hints["chain"] is Chain  # a new member keeps no released text form


def test_released_members_keep_the_text_form_of_chain() -> None:
    for name in (
        "add_rule",
        "remove_rule",
        "list_rules",
        "get_rule",
        "flush_chain",
        "set_default_policy",
        "get_default_policy",
        "get_rule_counters",
    ):
        hints = typing.get_type_hints(getattr(PacketFilter, name))
        assert hints["chain"] == Chain | str, name


def test_rule_counters_accept_zero_and_large() -> None:
    assert RuleCounters(0, 0).packets == 0
    big = 2**63
    assert RuleCounters(big, big * 2).bytes == big * 2
