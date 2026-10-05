"""The released QosRule.match text and the QosClassifier it spells; free text has none."""

from __future__ import annotations

import pytest
from testoperations.pairs import (
    parse_qos_classifier,
    qos_rule_classifier,
)
from testprotocols.models import PortRange, QosClassifier, QosRule, RuleProtocol


def _port(n: int) -> tuple[PortRange, ...]:
    return (PortRange.single(n),)


# every form the released producers write
RELEASED = [
    ("vlan=244, protocol=udp", QosClassifier(vlan=244, protocol=RuleProtocol.UDP)),
    ("vlan=241", QosClassifier(vlan=241)),
    (
        "vlan=10,protocol=tcp,dstPort=80",
        QosClassifier(vlan=10, protocol=RuleProtocol.TCP, dst_ports=_port(80)),
    ),
    ("vlan=100,protocol=any", QosClassifier(vlan=100, protocol=RuleProtocol.ANY)),
    ("protocol=udp", QosClassifier(protocol=RuleProtocol.UDP)),
    (
        "protocol=udp,srcPort=53",
        QosClassifier(protocol=RuleProtocol.UDP, src_ports=_port(53)),
    ),
    ("srcPortRange=1000-2000", QosClassifier(src_ports=(PortRange(1000, 2000),))),
    ("dstPortRange=8000-8100", QosClassifier(dst_ports=(PortRange(8000, 8100),))),
    ("protocol=TCP", QosClassifier(protocol=RuleProtocol.TCP)),
]


@pytest.mark.parametrize(("text", "expected"), RELEASED)
def test_every_released_form_parses(text: str, expected: QosClassifier) -> None:
    assert parse_qos_classifier(text) == expected
    assert qos_rule_classifier(QosRule(name="r", match=text)) == expected


def test_a_range_may_be_written_under_either_port_key() -> None:
    assert parse_qos_classifier("dstPort=80-90") == QosClassifier(dst_ports=(PortRange(80, 90),))


@pytest.mark.parametrize(
    "text",
    [
        "vlan 10",
        "match anything you like",
        "vlan=ten",
        "vlan=0",
        "vlan=5000",
        "protocol=sctp",
        "dstPort=http",
        "dstPort=0",
        "dstPortRange=90-80",
        "colour=red",
        "vlan=10,colour=red",
        "vlan=10,,protocol=tcp",
    ],
)
def test_free_text_has_no_classifier(text: str) -> None:
    assert parse_qos_classifier(text) is None


def test_empty_text_is_every_frame() -> None:
    assert parse_qos_classifier("") is None
    assert parse_qos_classifier("  ") is None


@pytest.mark.parametrize(
    "text",
    [
        "vlan=10,vlan=20",
        "protocol=tcp,protocol=udp",
        "dstPort=80,dstPort=81",
        "dstPort=80,dstPortRange=90-100",
        "srcPortRange=1-2,srcPort=3",
    ],
)
def test_a_repeated_key_raises(text: str) -> None:
    with pytest.raises(ValueError, match="given twice"):
        parse_qos_classifier(text)
