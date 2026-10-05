"""testoperations reads a record's text field and its typed twin the same way, whichever form
the driver filled: text only (a released driver), typed only (a new driver) or both."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from testoperations._compat import (
    firewall_rule_dst_ports,
    l3_rule_dst_ports,
    l3_rule_src_ports,
    nat_rule_dst_ports,
    nat_rule_translated_ports,
    qos_rule_classifier,
    security_event_timestamp,
)
from testprotocols.models import (
    FirewallRule,
    L3Rule,
    NatRule,
    PortRange,
    QosClassifier,
    QosRule,
    RuleAction,
    RuleProtocol,
    SecurityAction,
    SecurityEvent,
    ThreatCategory,
)

_PORTS = (PortRange.single(22), PortRange(80, 90))
_TEXT = "22,80-90"


def _rule(dst_port: str | None, dst_ports: tuple[PortRange, ...] | None) -> FirewallRule:
    return FirewallRule(
        name="r",
        action="allow",
        protocol="tcp",
        src_cidr="any",
        dst_cidr="any",
        dst_port=dst_port,
        dst_ports=dst_ports,
    )


def _nat(**ports: object) -> NatRule:
    return NatRule(name="n", mode="dnat", interface="wan0", **ports)  # type: ignore[arg-type]


def _l3(**ports: object) -> L3Rule:
    return L3Rule(action=RuleAction.DENY, **ports)  # type: ignore[arg-type]


def _event(ts: str | None, timestamp: datetime | None) -> SecurityEvent:
    return SecurityEvent(
        ts=ts,
        src_ip="192.0.2.1",
        dst_ip="198.51.100.1",
        protocol=RuleProtocol.TCP,
        action=SecurityAction.BLOCKED,
        category=ThreatCategory.MALWARE,
        timestamp=timestamp,
    )


def _qos(match: str | None, classifier: QosClassifier | None) -> QosRule:
    return QosRule(name="q", match=match, classifier=classifier)


def _same_either_form[R](
    read: Callable[[R], object],
    text_only: R,
    typed_only: R,
    both: R,
    expected: object,
) -> None:
    assert read(text_only) == expected
    assert read(typed_only) == expected
    assert read(both) == expected


def test_reads_accept_either_form() -> None:
    _same_either_form(
        firewall_rule_dst_ports,
        _rule(_TEXT, None),
        _rule(None, _PORTS),
        _rule(_TEXT, _PORTS),
        _PORTS,
    )
    _same_either_form(
        nat_rule_dst_ports,
        _nat(dst_port=_TEXT),
        _nat(dst_ports=_PORTS),
        _nat(dst_port=_TEXT, dst_ports=_PORTS),
        _PORTS,
    )
    _same_either_form(
        nat_rule_translated_ports,
        _nat(translated_port="8080"),
        _nat(translated_ports=(PortRange.single(8080),)),
        _nat(translated_port="8080", translated_ports=(PortRange.single(8080),)),
        (PortRange.single(8080),),
    )
    _same_either_form(
        l3_rule_src_ports,
        _l3(src_port=_TEXT),
        _l3(src_ports=_PORTS),
        _l3(src_port=_TEXT, src_ports=_PORTS),
        _PORTS,
    )
    _same_either_form(
        l3_rule_dst_ports,
        _l3(dst_port=_TEXT),
        _l3(dst_ports=_PORTS),
        _l3(dst_port=_TEXT, dst_ports=_PORTS),
        _PORTS,
    )
    when = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    _same_either_form(
        security_event_timestamp,
        _event("2026-01-02T03:04:05Z", None),
        _event(None, when),
        _event("2026-01-02T03:04:05+00:00", when),
        when,
    )
    classifier = QosClassifier(
        vlan=10, protocol=RuleProtocol.UDP, dst_ports=(PortRange(5060, 5061),)
    )
    _same_either_form(
        qos_rule_classifier,
        _qos("vlan=10,protocol=udp,dstPortRange=5060-5061", None),
        _qos(None, classifier),
        _qos("vlan=10,protocol=udp,dstPortRange=5060-5061", classifier),
        classifier,
    )


def test_the_any_spelling_and_the_empty_tuple_agree() -> None:
    assert firewall_rule_dst_ports(_rule("any", None)) == ()
    assert firewall_rule_dst_ports(_rule(None, ())) == ()
    assert l3_rule_dst_ports(_l3(dst_port="any")) == ()
    assert nat_rule_dst_ports(_nat(dst_port="")) == ()
    assert nat_rule_dst_ports(_nat(dst_port="any")) == ()


def test_released_defaults_read_as_the_released_default() -> None:
    # L3Rule's released default text is "any": every port, the empty tuple.
    assert l3_rule_src_ports(_l3()) == ()
    assert l3_rule_dst_ports(_l3()) == ()
    # NatRule's released default text is "": no port, the empty tuple.
    assert nat_rule_dst_ports(_nat()) == ()
    assert nat_rule_translated_ports(_nat()) == ()


def test_the_typed_form_wins_over_a_default_text() -> None:
    # A typed-only producer leaves the text at its released default; the typed form is read.
    assert l3_rule_dst_ports(_l3(dst_ports=_PORTS)) == _PORTS
    assert nat_rule_dst_ports(_nat(dst_ports=_PORTS)) == _PORTS


def test_text_set_to_none_reads_the_released_default() -> None:
    # A producer may pass None for a defaulted text field and leave the typed form unfilled.
    assert l3_rule_src_ports(_l3(src_port=None)) == ()
    assert l3_rule_dst_ports(_l3(dst_port=None)) == ()
    assert nat_rule_dst_ports(_nat(dst_port=None)) == ()
    assert nat_rule_translated_ports(_nat(translated_port=None)) == ()


def test_neither_filled_on_a_released_required_field_raises() -> None:
    with pytest.raises(ValueError, match=r"FirewallRule\.dst_port"):
        firewall_rule_dst_ports(_rule(None, None))


def test_an_absent_value_is_a_filled_value() -> None:
    # The typed twin of ``ts`` and of ``match`` holds ``None`` as a value (no time reported;
    # every frame), so a record whose two fields are ``None`` reads as that value.
    assert security_event_timestamp(_event(None, None)) is None
    assert security_event_timestamp(_event("", None)) is None
    assert qos_rule_classifier(_qos(None, None)) is None
    assert qos_rule_classifier(_qos("", None)) is None


def test_free_qos_text_has_no_classifier() -> None:
    assert qos_rule_classifier(_qos("vlan 10", None)) is None


def test_malformed_text_raises() -> None:
    with pytest.raises(ValueError, match="port"):
        firewall_rule_dst_ports(_rule("http", None))
    with pytest.raises(ValueError, match="timestamp"):
        security_event_timestamp(_event("yesterday", None))


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
def test_released_timestamp_spellings_parse(text: str) -> None:
    assert security_event_timestamp(_event(text, None)) == datetime.fromisoformat(text)


def test_a_naive_timestamp_text_stays_naive() -> None:
    when = security_event_timestamp(_event("2026-10-04T12:30:05", None))
    assert when is not None
    assert when.tzinfo is None
