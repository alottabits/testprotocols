"""L3Rule ports and SecurityEvent time: a released text field next to its typed form."""

from __future__ import annotations

from datetime import datetime

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
    return L3Rule(**{"action": RuleAction.DENY, **kw})  # type: ignore[arg-type]  # the keyword values are `object`


def test_l3_ports_default_to_the_released_text() -> None:
    r = _l3()
    assert (r.src_ports, r.dst_ports, r.src_port, r.dst_port) == (None, None, "any", "any")


def test_l3_released_positional_construction_still_works() -> None:
    r = L3Rule(RuleAction.ALLOW, RuleProtocol.TCP, "any", "1024", "10.0.0.0/24", "443")
    assert (r.src_port, r.dst_port, r.dst_cidr) == ("1024", "443", "10.0.0.0/24")
    assert (r.src_ports, r.dst_ports) == (None, None)


def test_l3_each_form_is_stored_as_given() -> None:
    r = _l3(src_port="22, 80", dst_ports=(PortRange(53, 53),))
    assert (r.src_port, r.src_ports) == ("22, 80", None)
    assert (r.dst_port, r.dst_ports) == ("any", (PortRange.single(53),))


def _event(**kw: object) -> SecurityEvent:
    base: dict[str, object] = {
        "ts": None,
        "src_ip": "10.0.0.1",
        "dst_ip": "10.0.0.2",
        "protocol": RuleProtocol.TCP,
        "action": SecurityAction.BLOCKED,
        "category": ThreatCategory.MALWARE,
    }
    return SecurityEvent(**{**base, **kw})  # type: ignore[arg-type]  # the keyword values are `object`


def test_event_released_positional_construction_still_works() -> None:
    e = SecurityEvent(
        "2026-10-04T12:30:05Z",
        "10.0.0.1",
        "10.0.0.2",
        RuleProtocol.UDP,
        SecurityAction.ALLOWED,
        ThreatCategory.BOTNET,
        "d",
    )
    assert (e.ts, e.timestamp) == ("2026-10-04T12:30:05Z", None)
    assert (e.src_ip, e.description, e.category) == ("10.0.0.1", "d", ThreatCategory.BOTNET)


def test_event_fields_after_ts_stay_required() -> None:
    with pytest.raises(TypeError, match="src_ip"):
        SecurityEvent(ts="")  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]  # the missing argument is the check


def test_event_naive_timestamp_stays_naive() -> None:
    e = _event(timestamp=datetime(2026, 10, 4, 12, 30, 5))
    assert e.timestamp is not None
    assert e.timestamp.tzinfo is None
    assert e.ts is None
