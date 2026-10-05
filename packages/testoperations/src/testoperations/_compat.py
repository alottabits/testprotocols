"""Read a record field that has a released text form and a typed form.

During a deprecation period a record keeps a released field that holds a grammar as text
(ports, a timestamp, a QoS classifier) next to its typed successor, and a driver fills
either, or both. The readers here give one answer whichever form the driver filled: the
typed field when it is filled, else the text field parsed, else what the released default
meant (or ``ValueError`` naming the record and field, when the released field was
required). No other operation reads either field of such a pair directly. The readers go
with the text fields at removal.

The parsers and formatters of the released text forms live here too.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime
from typing import assert_never, cast

from testprotocols.models import (
    ApplicationCategory,
    ApplicationMatch,
    CategoryMatch,
    FirewallRule,
    HostMatch,
    IpRangeMatch,
    L3Rule,
    L7MatchType,
    NatRule,
    PortMatch,
    PortRange,
    QosClassifier,
    QosRule,
    RuleProtocol,
    SecurityEvent,
    TrafficMatch,
)

_MAX_PORT = 65535

# --- ports -------------------------------------------------------------------------------


def _port_number(text: str) -> int:
    if not (text.isascii() and text.isdigit()):
        raise ValueError(f"{text!r} is not a port number")
    number = int(text)
    if not 1 <= number <= _MAX_PORT:
        raise ValueError(f"port {number} is outside 1-{_MAX_PORT}")
    return number


def _port_range(first: int, last: int) -> PortRange:
    if first > last:
        raise ValueError(f"port range {first}-{last}: first is above last")
    return PortRange(first, last)


def parse_port_ranges(text: str) -> tuple[PortRange, ...]:
    """Parse the released port grammar into ranges.

    ``"any"`` gives ``()``; otherwise a comma list of ``"80"`` or ``"80-90"``
    items (blanks around items are ignored). Anything else, including the
    empty text, raises ``ValueError``.
    """
    if text == "any":
        return ()
    ranges: list[PortRange] = []
    for item in text.split(","):
        first, dash, last = item.strip().partition("-")
        try:
            low = _port_number(first)
            ranges.append(_port_range(low, _port_number(last) if dash else low))
        except ValueError as bad:
            raise ValueError(f"malformed port spec {text!r}: {bad}") from None
    return tuple(ranges)


def format_port_ranges(ranges: tuple[PortRange, ...]) -> str:
    """The released text of *ranges*; ``()`` gives ``"any"``."""
    return ",".join(str(r) for r in ranges) if ranges else "any"


def port_tuple(value: object) -> tuple[PortRange, ...]:
    """*value* as a tuple of :class:`PortRange`.

    A list is converted to a tuple. A string or bytes (the released text passed where the
    typed form belongs), another non-iterable, or an item that is not a ``PortRange`` (a
    bare port number) raises ``TypeError``.
    """
    if isinstance(value, str | bytes) or not isinstance(value, Iterable):
        raise TypeError(f"port ranges take a tuple of PortRange, not {value!r}")
    ranges: list[PortRange] = []
    for item in cast("Iterable[object]", value):
        if not isinstance(item, PortRange):
            raise TypeError(f"port ranges take a tuple of PortRange, not {item!r}")
        ranges.append(item)
    return tuple(ranges)


def parse_nat_port_ranges(text: str) -> tuple[PortRange, ...]:
    """Parse a released ``NatRule`` port text: ``""`` (no port) gives ``()``; otherwise as
    :func:`parse_port_ranges` (``"any"`` gives ``()`` too)."""
    return () if text == "" else parse_port_ranges(text)


def ports_of(
    typed: tuple[PortRange, ...] | None,
    text: str | None,
    *,
    unset: str | None,
    owner: str,
    field: str,
    parse: Callable[[str], tuple[PortRange, ...]] = parse_port_ranges,
) -> tuple[PortRange, ...]:
    """The ports a driver gave in either form.

    *unset* is the released default's text (``"any"``, ``""``) when the released field had
    one, and ``None`` when the released field was required: then neither form filled raises
    ``ValueError`` naming *owner* and *field*. *parse* reads the text form.
    """
    if typed is not None:
        return typed
    if text is not None:
        return parse(text)
    if unset is None:
        raise ValueError(
            f"{owner}.{field}: neither the ports nor their released text form is filled"
        )
    return parse(unset)


def firewall_rule_dst_ports(rule: FirewallRule) -> tuple[PortRange, ...]:
    """*rule*'s destination ports (``()`` is any port). The released ``dst_port`` was
    required, so a rule with neither form filled raises ``ValueError``."""
    return ports_of(
        rule.dst_ports, rule.dst_port, unset=None, owner="FirewallRule", field="dst_port"
    )


def nat_rule_dst_ports(rule: NatRule) -> tuple[PortRange, ...]:
    """*rule*'s matched destination ports (``()`` is no port: any). Neither form filled
    reads as the released default ``""``."""
    return ports_of(
        rule.dst_ports,
        rule.dst_port,
        unset="",
        owner="NatRule",
        field="dst_port",
        parse=parse_nat_port_ranges,
    )


def nat_rule_translated_ports(rule: NatRule) -> tuple[PortRange, ...]:
    """*rule*'s translated ports (``()`` is no port). Neither form filled reads as the
    released default ``""``."""
    return ports_of(
        rule.translated_ports,
        rule.translated_port,
        unset="",
        owner="NatRule",
        field="translated_port",
        parse=parse_nat_port_ranges,
    )


def l3_rule_src_ports(rule: L3Rule) -> tuple[PortRange, ...]:
    """*rule*'s source ports (``()`` is any port). Neither form filled reads as the
    released default ``"any"``."""
    return ports_of(rule.src_ports, rule.src_port, unset="any", owner="L3Rule", field="src_port")


def l3_rule_dst_ports(rule: L3Rule) -> tuple[PortRange, ...]:
    """*rule*'s destination ports (``()`` is any port). Neither form filled reads as the
    released default ``"any"``."""
    return ports_of(rule.dst_ports, rule.dst_port, unset="any", owner="L3Rule", field="dst_port")


# --- timestamp ---------------------------------------------------------------------------


def parse_timestamp(text: str) -> datetime | None:
    """Parse a released ISO-8601 timestamp text; ``""`` (no time) gives ``None``. Text that
    is not ISO-8601 raises ``ValueError``."""
    if text == "":
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        raise ValueError(f"malformed ISO-8601 timestamp {text!r}") from None


def timestamp_of(typed: datetime | None, text: str | None) -> datetime | None:
    """The instant a driver gave in either form, or ``None`` for no time reported.

    The typed form holds ``None`` as a value (no time reported), so a record with neither
    form filled reads as ``None``.
    """
    if typed is not None:
        return typed
    if text is not None:
        return parse_timestamp(text)
    return None


def security_event_timestamp(event: SecurityEvent) -> datetime | None:
    """When *event* happened, or ``None`` when the product reports no time."""
    return timestamp_of(event.timestamp, event.ts)


# --- QoS classifier ----------------------------------------------------------------------

# The keys of the released ``QosRule.match`` text, as the released producers write them.
_QOS_KEYS = ("vlan", "protocol", "srcPort", "srcPortRange", "dstPort", "dstPortRange")
_MAX_VLAN = 4094


def _qos_port(value: str) -> PortRange:
    first, dash, last = value.partition("-")
    low = _port_number(first)
    return _port_range(low, _port_number(last) if dash else low)


def _qos_vlan(value: str) -> int:
    if not (value.isascii() and value.isdigit()) or not 1 <= int(value) <= _MAX_VLAN:
        raise ValueError(f"{value!r} is not a VLAN id")
    return int(value)


def parse_qos_classifier(text: str) -> QosClassifier | None:
    """The classifier the released ``QosRule.match`` text spells, or ``None``.

    The released contract gave the text no grammar. Text that is a comma list of
    ``key=value`` terms over the keys the released producers write (a VLAN, a protocol in
    any letter case, source and destination ports, a port or an ``a-b`` range) gives a
    classifier. Anything else (free text such as ``"vlan 10"``, another key, a value that is
    not a VLAN, protocol or port) has no classifier: ``None``. The empty text is ``None`` as
    well (every frame). A repeated key, or both the port and the range key of one
    direction, raises ``ValueError``.
    """
    body = text.strip()
    if body == "":
        return None
    terms: list[tuple[str, str]] = []
    for term in body.split(","):
        key, equals, value = term.strip().partition("=")
        if not equals or key not in _QOS_KEYS:
            return None
        terms.append((key, value.strip()))
    seen: dict[str, str] = {}
    for key, value in terms:
        group = key.removesuffix("Range")
        if group in seen:
            raise ValueError(f"QosRule.match {text!r}: the term {group!r} is given twice")
        seen[group] = value
    try:
        vlan = _qos_vlan(seen["vlan"]) if "vlan" in seen else None
        protocol = RuleProtocol(seen["protocol"].lower()) if "protocol" in seen else None
        src = (_qos_port(seen["srcPort"]),) if "srcPort" in seen else ()
        dst = (_qos_port(seen["dstPort"]),) if "dstPort" in seen else ()
    except ValueError:
        return None
    return QosClassifier(vlan=vlan, protocol=protocol, src_ports=src, dst_ports=dst)


def _qos_port_text(key: str, ranges: tuple[PortRange, ...]) -> list[str]:
    if len(ranges) > 1:
        raise ValueError(f"the released QoS text holds one {key} range, not {len(ranges)}")
    return [
        f"{key}={r.first}" if r.first == r.last else f"{key}Range={r.first}-{r.last}"
        for r in ranges
    ]


def format_qos_classifier(value: QosClassifier | None) -> str:
    """The released ``QosRule.match`` text of *value*; ``None`` gives ``""`` (every frame).
    A classifier with more than one range in a direction raises ``ValueError``: the
    released text spells one."""
    if value is None:
        return ""
    terms: list[str] = []
    if value.vlan is not None:
        terms.append(f"vlan={value.vlan}")
    if value.protocol is not None:
        terms.append(f"protocol={value.protocol.value}")
    terms += _qos_port_text("srcPort", value.src_ports)
    terms += _qos_port_text("dstPort", value.dst_ports)
    return ",".join(terms)


def classifier_of(typed: QosClassifier | None, text: str | None) -> QosClassifier | None:
    """The classifier a driver gave in either form, or ``None`` for every frame (or a
    released text that spells no classifier).

    The typed form holds ``None`` as a value (every frame), so a record with neither form
    filled reads as ``None``.
    """
    if typed is not None:
        return typed
    if text is not None:
        return parse_qos_classifier(text)
    return None


def qos_rule_classifier(rule: QosRule) -> QosClassifier | None:
    """The traffic *rule* selects (``None``: every frame, or a text with no classifier)."""
    return classifier_of(rule.classifier, rule.match)


# --- traffic match -----------------------------------------------------------------------

# the released port text "any" as a port match: every port
_EVERY_PORT = PortRange(1, _MAX_PORT)


def traffic_match(match_type: L7MatchType, value: str) -> TrafficMatch:
    """The :data:`~testprotocols.models.TrafficMatch` the released ``(match_type, value)``
    pair spells.

    ``value`` is an application name, an ``ApplicationCategory`` value, a host, a
    port text (``"80"``, ``"8000-8100"``, ``"22,80-90"``; ``"any"`` is every port,
    ``1-65535``) or an address range, by ``match_type``. Raises ``ValueError`` for a
    value that names no match: an empty one, an unknown category, or a port text
    that names no port number (a service name such as ``"http"``).
    """
    kind = L7MatchType(match_type)
    if kind is not L7MatchType.PORT and value == "":
        raise ValueError(f"an empty {kind.value} names no match")
    match kind:
        case L7MatchType.APPLICATION:
            return ApplicationMatch(value)
        case L7MatchType.APPLICATION_CATEGORY:
            return CategoryMatch(ApplicationCategory(value))
        case L7MatchType.HOST:
            return HostMatch(value)
        case L7MatchType.PORT:
            return PortMatch(parse_port_ranges(value) or (_EVERY_PORT,))
        case L7MatchType.IP_RANGE:
            return IpRangeMatch(value)
        case _:
            assert_never(kind)


def match_fields(match: TrafficMatch) -> tuple[L7MatchType, str]:
    """The released ``(match_type, value)`` pair of *match*; the inverse of
    :func:`traffic_match` (port text in canonical form)."""
    match match:
        case ApplicationMatch(name=name):
            return L7MatchType.APPLICATION, name
        case CategoryMatch(category=category):
            return L7MatchType.APPLICATION_CATEGORY, str(category)
        case HostMatch(host=host):
            return L7MatchType.HOST, host
        case PortMatch(ports=ports):
            return L7MatchType.PORT, format_port_ranges(ports)
        case IpRangeMatch(cidr=cidr):
            return L7MatchType.IP_RANGE, cidr
        case _:
            assert_never(match)
