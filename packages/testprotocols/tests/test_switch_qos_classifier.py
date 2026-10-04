"""QosRule.match as a typed QosClassifier (shape 4(ii)); free text has no classifier."""

from __future__ import annotations

import dataclasses
import warnings

import pytest
from testprotocols.models import PortRange, QosClassifier, QosRule, RuleProtocol

pytestmark = pytest.mark.filterwarnings("error::DeprecationWarning")


def _c(**kw: object) -> QosClassifier:
    return QosClassifier(**kw)  # type: ignore[arg-type]


def _cls(rule: QosRule) -> QosClassifier | None:
    return rule.classifier


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
def test_every_released_form_parses_and_keeps_its_spelling(
    text: str, expected: QosClassifier
) -> None:
    with pytest.warns(DeprecationWarning, match=r"QosRule.match is deprecated; use classifier"):
        r = QosRule(name="r", match=text)
    assert r.classifier == expected
    assert r.match == text


def test_a_range_may_be_written_under_either_port_key() -> None:
    with pytest.warns(DeprecationWarning):
        r = QosRule(name="r", match="dstPort=80-90")
    assert r.classifier == QosClassifier(dst_ports=(PortRange(80, 90),))


def test_typed_classifier_writes_canonical_text() -> None:
    r = QosRule(
        name="r",
        classifier=QosClassifier(
            vlan=10, protocol=RuleProtocol.TCP, src_ports=_port(53), dst_ports=(PortRange(80, 90),)
        ),
    )
    assert r.match == "vlan=10,protocol=tcp,srcPort=53,dstPortRange=80-90"
    assert QosRule(name="r", classifier=QosClassifier(vlan=5)).match == "vlan=5"


def test_typed_classifier_text_round_trips() -> None:
    for _, expected in RELEASED:
        r = QosRule(name="r", classifier=expected)
        with pytest.warns(DeprecationWarning):
            assert QosRule(name="r", match=r.match).classifier == expected


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
def test_free_text_has_no_classifier_and_stays_as_given(text: str) -> None:
    with pytest.warns(DeprecationWarning):
        r = QosRule(name="r", match=text)
    assert r.classifier is None
    assert r.match == text


def test_empty_text_and_no_classifier_are_every_frame() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        r = QosRule(name="all")
        assert (r.match, r.classifier) == ("", None)
        assert QosRule("all", "").classifier is None
        assert QosRule(name="all", classifier=QosClassifier()).classifier is None


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
        QosRule(name="r", match=text)


def test_released_positional_construction_still_works() -> None:
    with pytest.warns(DeprecationWarning):
        r = QosRule("r", "vlan=10", 26, None)
    assert (r.dscp, r.cos, r.classifier) == (26, None, QosClassifier(vlan=10))


def test_disagreeing_construction_raises_and_agreeing_is_silent() -> None:
    with pytest.raises(ValueError, match="disagree"):
        QosRule(name="r", match="vlan=10", classifier=QosClassifier(vlan=11))
    r = QosRule(name="r", match="vlan=10", classifier=QosClassifier(vlan=10))
    assert r.match == "vlan=10"


def test_wrong_types_and_bounds() -> None:
    with pytest.raises(TypeError):
        QosRule(name="r", classifier="vlan=10")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        QosRule(name="r", match=80)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        _c(vlan=True)
    with pytest.raises(ValueError, match="vlan"):
        _c(vlan=4095)
    with pytest.raises(TypeError):
        _c(dst_ports="80")
    with pytest.raises(ValueError, match="one port range per direction"):
        QosRule(name="r", classifier=QosClassifier(dst_ports=(PortRange(1, 2), PortRange(5, 6))))


def test_classifier_protocol_converts_a_named_string() -> None:
    with pytest.warns(DeprecationWarning, match="QosClassifier.protocol"):
        c = _c(protocol="tcp")
    assert c.protocol is RuleProtocol.TCP
    with pytest.raises(ValueError, match="not one of"):
        _c(protocol="sctp")


def test_replace_side_that_changed_wins() -> None:
    r = QosRule(name="r", classifier=QosClassifier(vlan=10))
    typed = dataclasses.replace(r, classifier=QosClassifier(vlan=20))
    assert typed.match == "vlan=20"
    with pytest.warns(DeprecationWarning):
        texted = dataclasses.replace(r, match="vlan=30, protocol=TCP")
    assert texted.classifier == QosClassifier(vlan=30, protocol=RuleProtocol.TCP)
    assert texted.match == "vlan=30, protocol=TCP"
    assert dataclasses.replace(r, dscp=10).classifier == r.classifier
    assert dataclasses.replace(r, classifier=None).match == ""
    with pytest.warns(DeprecationWarning):
        free = dataclasses.replace(r, match="vlan 10")
    assert free.classifier is None
    assert free.match == "vlan 10"


def test_assignment_resyncs_both_ways_and_keeps_free_text() -> None:
    r = QosRule(name="r")
    r.classifier = QosClassifier(dst_ports=(PortRange(1, 10),))
    assert r.match == "dstPortRange=1-10"
    with pytest.warns(DeprecationWarning):
        r.match = "protocol=UDP"
    assert r.classifier == QosClassifier(protocol=RuleProtocol.UDP)
    assert r.match == "protocol=UDP"
    with pytest.raises(ValueError, match="given twice"):
        r.match = "vlan=1,vlan=2"
    assert r.match == "protocol=UDP"
    with pytest.warns(DeprecationWarning):
        r.match = "vlan 10"
    assert _cls(r) is None
    assert r.match == "vlan 10"
    r.classifier = None
    assert r.match == "vlan 10"  # nothing lost
    r.classifier = QosClassifier(vlan=3)
    assert r.match == "vlan=3"
    r.classifier = None
    assert r.match == ""


def test_reassigning_the_same_value_changes_nothing() -> None:
    with pytest.warns(DeprecationWarning):
        r = QosRule(name="r", match="vlan=10,protocol=TCP")
    same = dataclasses.replace(r, classifier=r.classifier)
    r.classifier = r.classifier
    assert r.match == "vlan=10,protocol=TCP"
    assert same == r


def test_equal_when_built_from_either_side() -> None:
    with pytest.warns(DeprecationWarning):
        a = QosRule(name="r", match="vlan=10,protocol=tcp")
    assert a == QosRule(name="r", classifier=QosClassifier(vlan=10, protocol=RuleProtocol.TCP))
