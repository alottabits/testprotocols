"""QosRule: the released match text next to the typed QosClassifier."""

from __future__ import annotations

import pytest
from testprotocols.models import PortRange, QosClassifier, QosRule, RuleProtocol

pytestmark = pytest.mark.filterwarnings("error::DeprecationWarning")


def test_released_positional_construction_still_works() -> None:
    r = QosRule("r", "vlan=10", 26, None)
    assert (r.match, r.dscp, r.cos, r.classifier) == ("vlan=10", 26, None, None)


def test_each_form_is_stored_as_given() -> None:
    classifier = QosClassifier(vlan=10, protocol=RuleProtocol.TCP, dst_ports=(PortRange(80, 90),))
    typed = QosRule(name="r", match=None, classifier=classifier)
    assert (typed.match, typed.classifier) == (None, classifier)
    free = QosRule(name="r", match="vlan 10")
    assert (free.match, free.classifier) == ("vlan 10", None)


def test_match_stays_required() -> None:
    with pytest.raises(TypeError, match="match"):
        QosRule(name="r")  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]  # the missing argument is the check


def test_an_empty_classifier_places_no_restriction() -> None:
    assert QosClassifier() == QosClassifier(vlan=None, protocol=None, src_ports=(), dst_ports=())
