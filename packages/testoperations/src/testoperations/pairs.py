"""Read a record field that has a released text form and a typed form.

During a deprecation period a ``testprotocols`` record keeps a released field that holds a
grammar as text (ports, a timestamp, a QoS classifier) next to its typed successor, and a
driver fills either, or both, describing the same value. The record holds no code for the
pair, so a test reads it here and gets one answer whichever form the driver filled.

The read rule, for every reader: the typed field when it is filled, else the text field
parsed, else what the released default meant; where the released field was required and the
typed field cannot hold ``None`` as a value, neither form filled raises ``ValueError``
naming the record and field. A typed field that holds ``None`` as a value
(``SecurityEvent.timestamp``: no time reported; ``QosRule.classifier``: every frame) reads
as that ``None``.

Each reader and parser here is removed in the release that removes the text fields it
reads (see ``docs/architecture/precise-types-design.md``, "Deprecations"); from then on a
test reads the typed field directly.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from testprotocols.models import (
    FirewallRule,
    L3Rule,
    NatRule,
    PortRange,
    QosClassifier,
    QosRule,
    RuleProtocol,
    SecurityEvent,
)

__all__ = [
    "firewall_rule_dst_ports",
    "l3_rule_dst_ports",
    "l3_rule_src_ports",
    "nat_rule_dst_ports",
    "nat_rule_translated_ports",
    "parse_nat_port_ranges",
    "parse_port_ranges",
    "parse_qos_classifier",
    "parse_timestamp",
    "qos_rule_classifier",
    "security_event_timestamp",
]

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
    """Parse the released port text (``FirewallRule.dst_port``, ``L3Rule`` ports) into ranges.

    ``"any"`` gives ``()`` (any port); otherwise a comma list of ``"80"`` or ``"80-90"``
    items (blanks around items are ignored). Anything else, including the empty text,
    raises ``ValueError``.

    Removed in the release that removes the text fields.
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


def parse_nat_port_ranges(text: str) -> tuple[PortRange, ...]:
    """Parse a released ``NatRule`` port text: ``""`` (no port) gives ``()``; otherwise as
    :func:`parse_port_ranges` (``"any"`` gives ``()`` too).

    Removed in the release that removes the text fields.
    """
    return () if text == "" else parse_port_ranges(text)


def _ports_of(
    typed: tuple[PortRange, ...] | None,
    text: str | None,
    *,
    unset: str | None,
    record: str,
    field: str,
    parse: Callable[[str], tuple[PortRange, ...]] = parse_port_ranges,
) -> tuple[PortRange, ...]:
    """The typed form when filled, else the text parsed, else *unset* parsed (the released
    default's text); *unset* ``None`` (the released field was required) raises."""
    if typed is not None:
        return typed
    if text is not None:
        return parse(text)
    if unset is None:
        raise ValueError(
            f"{record}.{field}: neither the ports nor their released text form is filled"
        )
    return parse(unset)


def firewall_rule_dst_ports(rule: FirewallRule) -> tuple[PortRange, ...]:
    """*rule*'s destination ports (``()`` is any port).

    Read rule: ``dst_ports`` when filled, else ``dst_port`` parsed with
    :func:`parse_port_ranges`; the released ``dst_port`` was required, so a rule with
    neither form filled raises ``ValueError``. Malformed text raises ``ValueError``.

    Removed in the release that removes ``FirewallRule.dst_port``.
    """
    return _ports_of(
        rule.dst_ports, rule.dst_port, unset=None, record="FirewallRule", field="dst_port"
    )


def nat_rule_dst_ports(rule: NatRule) -> tuple[PortRange, ...]:
    """*rule*'s matched destination ports (``()`` is no port restriction).

    Read rule: ``dst_ports`` when filled, else ``dst_port`` parsed with
    :func:`parse_nat_port_ranges`, else (text ``None``) the released default ``""``, no
    port. Malformed text raises ``ValueError``.

    Removed in the release that removes ``NatRule.dst_port``.
    """
    return _ports_of(
        rule.dst_ports,
        rule.dst_port,
        unset="",
        record="NatRule",
        field="dst_port",
        parse=parse_nat_port_ranges,
    )


def nat_rule_translated_ports(rule: NatRule) -> tuple[PortRange, ...]:
    """*rule*'s translated ports (``()`` is no port).

    Read rule: ``translated_ports`` when filled, else ``translated_port`` parsed with
    :func:`parse_nat_port_ranges`, else (text ``None``) the released default ``""``, no
    port. Malformed text raises ``ValueError``.

    Removed in the release that removes ``NatRule.translated_port``.
    """
    return _ports_of(
        rule.translated_ports,
        rule.translated_port,
        unset="",
        record="NatRule",
        field="translated_port",
        parse=parse_nat_port_ranges,
    )


def l3_rule_src_ports(rule: L3Rule) -> tuple[PortRange, ...]:
    """*rule*'s source ports (``()`` is any port).

    Read rule: ``src_ports`` when filled, else ``src_port`` parsed with
    :func:`parse_port_ranges`, else (text ``None``) the released default ``"any"``.
    Malformed text raises ``ValueError``.

    Removed in the release that removes ``L3Rule.src_port``.
    """
    return _ports_of(rule.src_ports, rule.src_port, unset="any", record="L3Rule", field="src_port")


def l3_rule_dst_ports(rule: L3Rule) -> tuple[PortRange, ...]:
    """*rule*'s destination ports (``()`` is any port).

    Read rule: ``dst_ports`` when filled, else ``dst_port`` parsed with
    :func:`parse_port_ranges`, else (text ``None``) the released default ``"any"``.
    Malformed text raises ``ValueError``.

    Removed in the release that removes ``L3Rule.dst_port``.
    """
    return _ports_of(rule.dst_ports, rule.dst_port, unset="any", record="L3Rule", field="dst_port")


# --- timestamp ---------------------------------------------------------------------------


def parse_timestamp(text: str) -> datetime | None:
    """Parse a released ISO-8601 timestamp text (``SecurityEvent.ts``) with
    ``datetime.fromisoformat``; ``""`` (no time) gives ``None``. A timezone-naive text stays
    naive. Text that is not ISO-8601 raises ``ValueError``.

    Removed in the release that removes the text fields.
    """
    if text == "":
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        raise ValueError(f"malformed ISO-8601 timestamp {text!r}") from None


def security_event_timestamp(event: SecurityEvent) -> datetime | None:
    """When *event* happened, or ``None`` when the product reports no time.

    Read rule: ``timestamp`` when filled, else ``ts`` parsed with :func:`parse_timestamp`
    (``""`` is no time), else ``None``: the typed field holds ``None`` as a value (no time
    reported), so an event with neither form filled reads as ``None``. Malformed text raises
    ``ValueError``.

    Removed in the release that removes ``SecurityEvent.ts``.
    """
    if event.timestamp is not None:
        return event.timestamp
    if event.ts is not None:
        return parse_timestamp(event.ts)
    return None


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

    Removed in the release that removes the text fields.
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


def qos_rule_classifier(rule: QosRule) -> QosClassifier | None:
    """The traffic *rule* selects, or ``None`` for every frame.

    Read rule: ``classifier`` when filled, else ``match`` parsed with
    :func:`parse_qos_classifier` (text that spells no classifier reads as ``None``, and
    ``match`` keeps the text as given), else ``None``: the typed field holds ``None`` as a
    value (every frame), so a rule with neither form filled reads as ``None``.

    Removed in the release that removes ``QosRule.match``.
    """
    if rule.classifier is not None:
        return rule.classifier
    if rule.match is not None:
        return parse_qos_classifier(rule.match)
    return None
