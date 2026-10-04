"""L3Rule ports (shape 4(ii)) and SecurityEvent timestamp (shape 4(ii)) as typed fields."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta, timezone

import pytest
from testprotocols.models import (
    L3Rule,
    PortRange,
    RuleAction,
    RuleProtocol,
    SecurityAction,
    SecurityEvent,
    ThreatCategory,
)

pytestmark = pytest.mark.filterwarnings("error::DeprecationWarning")


def _l3(**kw: object) -> L3Rule:
    return L3Rule(**{"action": RuleAction.DENY, **kw})  # type: ignore[arg-type]


# --- M10: L3Rule ports ---


def test_l3_typed_ports_fill_the_text() -> None:
    r = _l3(
        src_ports=(PortRange(1024, 65535),), dst_ports=(PortRange.single(53), PortRange(80, 90))
    )
    assert (r.src_port, r.dst_port) == ("1024-65535", "53,80-90")


def test_l3_default_is_any_port() -> None:
    r = _l3()
    assert (r.src_ports, r.dst_ports, r.src_port, r.dst_port) == ((), (), "any", "any")


def test_l3_text_alone_warns_and_fills_typed() -> None:
    with pytest.warns(DeprecationWarning, match=r"L3Rule.dst_port is deprecated; use dst_ports"):
        r = _l3(dst_port="8000-8100")
    assert r.dst_ports == (PortRange(8000, 8100),)
    with pytest.warns(DeprecationWarning, match=r"L3Rule.src_port is deprecated; use src_ports"):
        r = _l3(src_port="22,80")
    assert r.src_ports == (PortRange.single(22), PortRange.single(80))


def test_l3_released_positional_construction_still_works() -> None:
    with pytest.warns(DeprecationWarning):
        r = L3Rule(RuleAction.ALLOW, RuleProtocol.TCP, "any", "1024", "10.0.0.0/24", "443")
    assert r.src_ports == (PortRange.single(1024),)
    assert r.dst_ports == (PortRange.single(443),)
    assert r.dst_cidr == "10.0.0.0/24"


def test_l3_disagreeing_construction_raises() -> None:
    with pytest.raises(ValueError, match="disagree"):
        _l3(dst_port="80", dst_ports=(PortRange.single(81),))


def test_l3_replace_side_that_changed_wins() -> None:
    r = _l3(dst_ports=(PortRange.single(80),))
    typed = dataclasses.replace(r, dst_ports=(PortRange.single(443),))
    assert typed.dst_port == "443"
    with pytest.warns(DeprecationWarning):
        texted = dataclasses.replace(r, dst_port="8080")
    assert texted.dst_ports == (PortRange.single(8080),)
    assert dataclasses.replace(r, comment="x").dst_ports == r.dst_ports


def test_l3_assignment_resyncs_both_ways() -> None:
    r = _l3()
    r.dst_ports = (PortRange(1, 10),)
    assert r.dst_port == "1-10"
    with pytest.warns(DeprecationWarning):
        r.src_port = "53"
    assert r.src_ports == (PortRange.single(53),)
    r.src_ports = ()
    assert r.src_port == "any"


def test_l3_malformed_and_wrong_types() -> None:
    with pytest.raises(ValueError, match="malformed port spec"):
        _l3(dst_port="http")
    with pytest.raises(TypeError):
        _l3(dst_ports="80")
    r = _l3()
    with pytest.raises(TypeError):
        r.dst_port = 80  # type: ignore[assignment]
    assert r.dst_port == "any"


def test_l3_released_equality_between_the_two_builders() -> None:
    with pytest.warns(DeprecationWarning):
        a = _l3(dst_port="22, 80")
    assert a == _l3(dst_ports=(PortRange.single(22), PortRange.single(80)))


# --- M13: SecurityEvent timestamp ---


def _event(**kw: object) -> SecurityEvent:
    base: dict[str, object] = {
        "src_ip": "10.0.0.1",
        "dst_ip": "10.0.0.2",
        "protocol": RuleProtocol.TCP,
        "action": SecurityAction.BLOCKED,
        "category": ThreatCategory.SCAN,
    }
    return SecurityEvent(**{**base, **kw})  # type: ignore[arg-type]


def test_event_typed_timestamp_fills_ts() -> None:
    when = datetime(2026, 10, 4, 12, 30, 5, tzinfo=UTC)
    e = _event(timestamp=when)
    assert e.timestamp == when
    assert e.ts == "2026-10-04T12:30:05+00:00"


def test_event_ts_alone_warns_and_fills_timestamp() -> None:
    with pytest.warns(DeprecationWarning, match=r"SecurityEvent.ts is deprecated; use timestamp"):
        e = _event(ts="2026-10-04T12:30:05Z")
    assert e.timestamp == datetime(2026, 10, 4, 12, 30, 5, tzinfo=UTC)


def test_event_released_positional_construction_still_works() -> None:
    with pytest.warns(DeprecationWarning):
        e = SecurityEvent(
            "2026-10-04T12:30:05Z",
            "10.0.0.1",
            "10.0.0.2",
            RuleProtocol.UDP,
            SecurityAction.ALLOWED,
            ThreatCategory.BOTNET,
            "d",
        )
    assert (e.src_ip, e.description, e.category) == ("10.0.0.1", "d", ThreatCategory.BOTNET)


@pytest.mark.parametrize(
    "text",
    [
        "2026-10-04T12:30:05Z",
        "2026-10-04T12:30:05+00:00",
        "2026-10-04T12:30:05.250000+00:00",
        "2026-10-04T12:30:05",
        "2026-10-04T14:30:05+02:00",
        "2026-10-04 12:30:05",
    ],
)
def test_event_ts_text_is_kept_as_given(text: str) -> None:
    with pytest.warns(DeprecationWarning):
        e = _event(ts=text)
    assert e.ts == text
    assert e.timestamp == datetime.fromisoformat(text)


def test_event_naive_timestamp_stays_naive() -> None:
    e = _event(timestamp=datetime(2026, 10, 4, 12, 30, 5))
    assert e.timestamp is not None
    assert e.timestamp.tzinfo is None
    assert e.ts == "2026-10-04T12:30:05"
    with pytest.warns(DeprecationWarning):
        assert _event(ts="2026-10-04T12:30:05").timestamp == e.timestamp


def test_event_offset_timestamp_round_trips() -> None:
    zone = timezone(timedelta(hours=2))
    e = _event(timestamp=datetime(2026, 10, 4, 14, 30, tzinfo=zone))
    assert e.ts == "2026-10-04T14:30:00+02:00"


def test_event_no_timestamp_is_empty_text_and_none() -> None:
    e = _event()
    assert (e.ts, e.timestamp) == ("", None)


def test_event_disagreeing_construction_raises() -> None:
    with pytest.raises(ValueError, match="disagree"):
        _event(ts="2026-10-04T12:30:05Z", timestamp=datetime(2026, 1, 1, tzinfo=UTC))


def test_event_equal_instants_in_two_spellings_agree() -> None:
    when = datetime(2026, 10, 4, 12, 30, 5, tzinfo=UTC)
    e = _event(ts="2026-10-04T12:30:05Z", timestamp=when)
    assert e.ts == "2026-10-04T12:30:05Z"


def test_event_malformed_text_and_wrong_types() -> None:
    with pytest.raises(ValueError, match="ISO-8601"):
        _event(ts="yesterday")
    with pytest.raises(TypeError):
        _event(timestamp="2026-10-04T12:30:05Z")
    with pytest.raises(TypeError):
        _event(timestamp=1759581005)
    with pytest.raises(TypeError):
        _event(ts=5)


def test_event_replace_and_assignment_side_that_changed_wins() -> None:
    e = _event(timestamp=datetime(2026, 10, 4, 12, tzinfo=UTC))
    later = dataclasses.replace(e, timestamp=datetime(2026, 10, 5, 12, tzinfo=UTC))
    assert later.ts == "2026-10-05T12:00:00+00:00"
    with pytest.warns(DeprecationWarning):
        textual = dataclasses.replace(e, ts="2026-10-06T12:00:00Z")
    assert textual.timestamp == datetime(2026, 10, 6, 12, tzinfo=UTC)
    assert textual.ts == "2026-10-06T12:00:00Z"
    e.timestamp = datetime(2026, 10, 7, 12, tzinfo=UTC)
    assert e.ts == "2026-10-07T12:00:00+00:00"
    e.timestamp = None
    assert e.ts == ""
    with pytest.warns(DeprecationWarning):
        e.ts = "2026-10-08T12:00:00Z"
    assert e.timestamp == datetime(2026, 10, 8, 12, tzinfo=UTC)
    with pytest.raises(ValueError, match="ISO-8601"):
        e.ts = "nope"
    assert e.ts == "2026-10-08T12:00:00Z"


def test_event_required_fields_still_required() -> None:
    with pytest.raises(TypeError, match="missing"):
        SecurityEvent(ts="", src_ip="a")
    with pytest.raises(TypeError, match="missing"):
        SecurityEvent()


# --- fix round 1 ---


@pytest.mark.parametrize("bad", [80, None, 80.0, b"80", ("80",)])
def test_non_text_port_at_construction_is_a_type_error(bad: object) -> None:
    from testprotocols.models import FirewallRule, FirewallRuleAction, NatMode, NatRule

    with pytest.raises(TypeError, match="port text"):
        _l3(dst_port=bad)
    with pytest.raises(TypeError, match="port text"):
        _l3(src_port=bad)
    with pytest.raises(TypeError, match="port text"):
        FirewallRule("r", FirewallRuleAction.ALLOW, RuleProtocol.TCP, "any", "any", bad)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="port text"):
        NatRule(name="n", mode=NatMode.DNAT, interface="wan", dst_port=bad)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="port text"):
        NatRule(name="n", mode=NatMode.DNAT, interface="wan", translated_port=bad)  # type: ignore[arg-type]


def test_event_equal_instant_at_another_offset_rewrites_the_text() -> None:
    z = datetime(2026, 10, 4, 12, tzinfo=UTC)
    plus2 = datetime(2026, 10, 4, 14, tzinfo=timezone(timedelta(hours=2)))
    assert z == plus2
    with pytest.warns(DeprecationWarning):
        e = _event(ts="2026-10-04T12:00:00Z")
    via_replace = dataclasses.replace(e, timestamp=plus2)
    assert via_replace.ts == "2026-10-04T14:00:00+02:00"
    e.timestamp = plus2
    assert e.ts == "2026-10-04T14:00:00+02:00"
    assert e == via_replace


def test_event_reassigning_the_same_value_changes_nothing() -> None:
    with pytest.warns(DeprecationWarning):
        e = _event(ts="2026-10-04T12:00:00Z")
    same = dataclasses.replace(e, timestamp=e.timestamp)
    before = e.ts
    e.timestamp = e.timestamp
    assert e.ts == before == "2026-10-04T12:00:00Z"
    assert same == e


def test_event_non_text_ts_names_the_field() -> None:
    with pytest.raises(TypeError, match=r"SecurityEvent\.ts"):
        _event(ts=5)


def test_event_required_placeholder_has_a_readable_repr() -> None:
    defaults = {f.name: f.default for f in dataclasses.fields(SecurityEvent)}
    assert repr(defaults["src_ip"]) == "<required>"
