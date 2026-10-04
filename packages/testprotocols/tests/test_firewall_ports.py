"""FirewallRule and NatRule ports as PortRange (shape 4(ii)); RuleCounters (shape 5)."""

from __future__ import annotations

import dataclasses

import pytest
from testprotocols.models import (
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


def _rule(**kw: object) -> FirewallRule:
    base: dict[str, object] = {
        "name": "r",
        "action": FirewallRuleAction.ALLOW,
        "protocol": RuleProtocol.TCP,
        "src_cidr": "any",
        "dst_cidr": "any",
    }
    return FirewallRule(**{**base, **kw})  # type: ignore[arg-type]


def _ports(r: FirewallRule) -> tuple[PortRange, ...]:
    return r.dst_ports


def _nat(**kw: object) -> NatRule:
    return NatRule(**{"name": "n", "mode": NatMode.DNAT, "interface": "wan", **kw})  # type: ignore[arg-type]


pytestmark = pytest.mark.filterwarnings("error::DeprecationWarning")


# --- FirewallRule ---


def test_typed_ports_fill_the_text() -> None:
    r = _rule(dst_ports=(PortRange(80, 90), PortRange.single(22)))
    assert r.dst_port == "80-90,22"


def test_text_alone_warns_and_fills_typed() -> None:
    with pytest.warns(DeprecationWarning, match="FirewallRule.dst_port is deprecated"):
        r = _rule(dst_port="1024-65535")
    assert r.dst_ports == (PortRange(1024, 65535),)


def test_released_positional_construction_still_works() -> None:
    with pytest.warns(DeprecationWarning):
        r = FirewallRule("r", FirewallRuleAction.ALLOW, RuleProtocol.TCP, "any", "any", "443")
    assert r.dst_ports == (PortRange.single(443),)


def test_any_text_and_default_mean_any_port() -> None:
    assert _rule().dst_ports == ()
    assert _rule().dst_port == "any"
    # "any" is the text default, so giving it is indistinguishable from omitting it: silent
    assert _rule(dst_port="any").dst_ports == ()


def test_disagreeing_construction_raises() -> None:
    with pytest.raises(ValueError, match="disagree"):
        _rule(dst_port="80", dst_ports=(PortRange.single(81),))


def test_agreeing_construction_is_silent() -> None:
    r = _rule(dst_port="80", dst_ports=(PortRange.single(80),))
    assert r.dst_ports == (PortRange.single(80),)


def test_malformed_text_raises_before_warning() -> None:
    with pytest.raises(ValueError, match="malformed"):
        _rule(dst_port="http")


def test_typed_field_refuses_text() -> None:
    with pytest.raises(TypeError):
        _rule(dst_ports="80")


def test_replace_each_side_wins() -> None:
    r = _rule(dst_ports=(PortRange.single(80),))
    assert dataclasses.replace(r, dst_ports=(PortRange.single(81),)).dst_port == "81"
    with pytest.warns(DeprecationWarning):
        r2 = dataclasses.replace(r, dst_port="443")
    assert r2.dst_ports == (PortRange.single(443),)
    assert dataclasses.replace(r, name="x").dst_ports == r.dst_ports


def test_assignment_each_side_wins() -> None:
    r = _rule()
    r.dst_ports = (PortRange(1, 2),)
    assert r.dst_port == "1-2"
    with pytest.warns(DeprecationWarning):
        r.dst_port = "any"
    assert not _ports(r)
    with pytest.raises(ValueError):
        r.dst_port = "x"
    assert not _ports(r)
    with pytest.raises(TypeError):
        r.dst_port = 80  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue]


def test_enum_coercion_survives_the_sync_wiring() -> None:
    with pytest.warns(DeprecationWarning, match="FirewallRule.action"):
        r = _rule(action="deny")
    assert r.action is FirewallRuleAction.DENY
    with pytest.warns(DeprecationWarning, match="FirewallRule.protocol"):
        r.protocol = "udp"
    assert r.protocol is RuleProtocol.UDP
    with pytest.raises(ValueError):
        r.action = "bogus"


def test_equality_ignores_provenance() -> None:
    assert _rule(dst_ports=(PortRange.single(80),)) == _rule(dst_ports=(PortRange.single(80),))
    with pytest.warns(DeprecationWarning):
        assert _rule(dst_port="80") == _rule(dst_ports=(PortRange.single(80),))


# --- NatRule ---


def test_nat_default_ports_are_any_with_released_empty_text() -> None:
    n = _nat()
    assert (n.dst_ports, n.translated_ports) == ((), ())
    assert (n.dst_port, n.translated_port) == ("", "")


def test_nat_typed_fills_text_for_both_pairs() -> None:
    n = _nat(dst_ports=(PortRange.single(8080),), translated_ports=(PortRange.single(80),))
    assert (n.dst_port, n.translated_port) == ("8080", "80")


def test_nat_text_warns() -> None:
    with pytest.warns(DeprecationWarning, match="NatRule.dst_port is deprecated"):
        n = _nat(dst_port="8080")
    assert n.dst_ports == (PortRange.single(8080),)
    with pytest.warns(DeprecationWarning, match="NatRule.translated_port is deprecated"):
        n = _nat(translated_port="80")
    assert n.translated_ports == (PortRange.single(80),)


def test_nat_released_empty_and_any_text_still_work_and_normalise_to_empty() -> None:
    assert _nat(dst_port="", translated_port="").dst_ports == ()
    with pytest.warns(DeprecationWarning):
        n = _nat(dst_port="any")
    assert n.dst_ports == ()
    assert n.dst_port == ""


def test_nat_conflict_raises() -> None:
    with pytest.raises(ValueError, match="disagree"):
        _nat(translated_port="80", translated_ports=(PortRange.single(81),))


def test_nat_replace_and_assignment() -> None:
    n = _nat(dst_ports=(PortRange.single(80),), translated_ports=(PortRange.single(8080),))
    m = dataclasses.replace(n, translated_ports=(PortRange.single(9),))
    assert (m.dst_port, m.translated_port) == ("80", "9")
    with pytest.warns(DeprecationWarning):
        m = dataclasses.replace(n, dst_port="")
    assert (m.dst_ports, m.translated_ports) == ((), (PortRange.single(8080),))
    n.translated_ports = ()
    assert n.translated_port == ""
    with pytest.warns(DeprecationWarning):
        n.dst_port = "1-2"
    assert n.dst_ports == (PortRange(1, 2),)
    assert n.translated_ports == ()


def test_nat_enum_coercion_survives() -> None:
    with pytest.warns(DeprecationWarning, match="NatRule.mode"):
        n = _nat(mode="snat")
    assert n.mode is NatMode.SNAT


# --- RuleCounters ---


def test_rule_counters_hold_values_and_are_frozen() -> None:
    c = RuleCounters(packets=3, bytes=4)
    assert (c.packets, c.bytes) == (3, 4)
    assert RuleCounters(0, 0) == RuleCounters(0, 0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        c.packets = 1  # type: ignore[misc]


@pytest.mark.parametrize("bad", [-1])
def test_rule_counters_refuse_negative(bad: int) -> None:
    with pytest.raises(ValueError, match="packets"):
        RuleCounters(bad, 0)
    with pytest.raises(ValueError, match="bytes"):
        RuleCounters(0, bad)


@pytest.mark.parametrize("bad", [True, 1.0, "1", None])
def test_rule_counters_refuse_non_int(bad: object) -> None:
    with pytest.raises(TypeError, match="packets"):
        RuleCounters(bad, 0)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="bytes"):
        RuleCounters(0, bad)  # type: ignore[arg-type]


def test_new_counter_members_exist_and_old_remain() -> None:
    assert callable(PacketFilter.get_rule_counter_values)
    assert callable(PacketFilter.get_rule_counters)
    assert callable(Nat.get_nat_rule_counter_values)
    assert callable(Nat.get_nat_rule_counters)
