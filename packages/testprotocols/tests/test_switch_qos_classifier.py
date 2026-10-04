"""QosRule.match as a typed classifier (shape 4(ii))."""

from __future__ import annotations

import dataclasses
import warnings

import pytest
from testprotocols.models import (
    ApplicationMatch,
    HostMatch,
    IpRangeMatch,
    PortMatch,
    PortRange,
    QosRule,
)

pytestmark = pytest.mark.filterwarnings("error::DeprecationWarning")


def test_typed_classifier_fills_the_text() -> None:
    r = QosRule(name="dns", classifier=PortMatch((PortRange.single(53),)), dscp=46)
    assert r.match == "dstPort=53"
    r = QosRule(name="hi", classifier=PortMatch((PortRange(8000, 8100),)))
    assert r.match == "dstPortRange=8000-8100"
    r = QosRule(name="many", classifier=PortMatch((PortRange.single(22), PortRange(80, 90))))
    assert r.match == "dstPort=22,dstPortRange=80-90"


def test_text_alone_warns_and_fills_the_classifier() -> None:
    with pytest.warns(DeprecationWarning, match=r"QosRule.match is deprecated; use classifier"):
        r = QosRule(name="dns", match="dstPort=53")
    assert r.classifier == PortMatch((PortRange.single(53),))
    with pytest.warns(DeprecationWarning):
        r = QosRule(name="many", match="dstPort=22, dstPortRange=80-90")
    assert r.classifier == PortMatch((PortRange.single(22), PortRange(80, 90)))
    assert r.match == "dstPort=22,dstPortRange=80-90"


def test_no_classifier_is_the_empty_text() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        r = QosRule(name="all")
        assert (r.match, r.classifier) == ("", None)
        assert QosRule("all", "").classifier is None


def test_released_positional_construction_still_works() -> None:
    with pytest.warns(DeprecationWarning):
        r = QosRule("r", "dstPort=80", 26, None)
    assert (r.dscp, r.cos) == (26, None)


def test_disagreeing_construction_raises() -> None:
    with pytest.raises(ValueError, match="disagree"):
        QosRule(name="r", match="dstPort=80", classifier=PortMatch((PortRange.single(81),)))


def test_agreeing_construction_is_silent() -> None:
    r = QosRule(name="r", match="dstPort=80", classifier=PortMatch((PortRange.single(80),)))
    assert r.match == "dstPort=80"


@pytest.mark.parametrize(
    "text",
    [
        "vlan=10",
        "vlan=244, protocol=udp",
        "vlan=10,protocol=tcp,dstPort=80",
        "vlan=100,protocol=any",
        "protocol=udp",
        "protocol=udp,srcPort=53",
        "srcPort=53",
        "srcPortRange=1000-2000",
        "vlan 10",
        "dstPort=http",
        "dstPort=80,vlan=10",
        "dstPort=0",
        "dstPortRange=90-80",
        "dstPortRange=80",
        "dstPort=80-90",
        "dstPort=",
        "dstPort=80,,dstPort=81",
        "dstport=80",
    ],
)
def test_text_that_is_not_a_destination_port_expression_raises(text: str) -> None:
    with pytest.raises(ValueError, match="traffic classifier"):
        QosRule(name="r", match=text)


def test_only_a_port_match_can_classify() -> None:
    for other in (HostMatch("h"), ApplicationMatch("a"), IpRangeMatch("198.51.100.0/24")):
        with pytest.raises(ValueError, match="destination ports"):
            QosRule(name="r", classifier=other)
    with pytest.raises(TypeError):
        QosRule(name="r", classifier="dstPort=80")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        QosRule(name="r", match=80)  # type: ignore[arg-type]


def test_replace_side_that_changed_wins() -> None:
    r = QosRule(name="r", classifier=PortMatch((PortRange.single(80),)))
    typed = dataclasses.replace(r, classifier=PortMatch((PortRange.single(443),)))
    assert typed.match == "dstPort=443"
    with pytest.warns(DeprecationWarning):
        texted = dataclasses.replace(r, match="dstPort=8080")
    assert texted.classifier == PortMatch((PortRange.single(8080),))
    assert dataclasses.replace(r, dscp=10).classifier == r.classifier
    assert dataclasses.replace(r, classifier=None).match == ""


def test_assignment_resyncs_both_ways_and_refuses_bad_text() -> None:
    r = QosRule(name="r")
    r.classifier = PortMatch((PortRange(1, 10),))
    assert r.match == "dstPortRange=1-10"
    with pytest.warns(DeprecationWarning):
        r.match = "dstPort=53"
    assert r.classifier == PortMatch((PortRange.single(53),))
    with pytest.raises(ValueError, match="traffic classifier"):
        r.match = "vlan=10"
    assert r.match == "dstPort=53"
    r.classifier = None
    assert r.match == ""


def test_equal_when_built_from_either_side() -> None:
    with pytest.warns(DeprecationWarning):
        a = QosRule(name="r", match="dstPort=22, dstPort=80")
    assert a == QosRule(
        name="r", classifier=PortMatch((PortRange.single(22), PortRange.single(80)))
    )
