"""Read a record field that has a released text form and a typed form.

During a deprecation period a record keeps a released field that holds a grammar as text
(ports, a timestamp, a QoS classifier) next to its typed successor, and a driver fills
either, or both. The readers here give one answer whichever form the driver filled: the
typed field when it is filled, else the text field parsed, else what the released default
meant (or ``ValueError`` naming the record and field, when the released field was
required). No other operation reads either field of such a pair directly. The readers go
with the text fields at removal.

The parsers of the released text forms live here too, and :func:`coerce_enum`, which
converts an operation's own released string parameter to its enum.
"""

from __future__ import annotations

import re
import warnings
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from enum import Enum, IntEnum
from typing import cast

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


def parse_nat_port_ranges(text: str) -> tuple[PortRange, ...]:
    """Parse a released ``NatRule`` port text: ``""`` (no port) gives ``()``; otherwise as
    :func:`parse_port_ranges` (``"any"`` gives ``()`` too)."""
    return () if text == "" else parse_port_ranges(text)


def ports_of(
    typed: tuple[PortRange, ...] | None,
    text: str | None,
    *,
    unset: str | None,
    record: str,
    field: str,
    parse: Callable[[str], tuple[PortRange, ...]] = parse_port_ranges,
) -> tuple[PortRange, ...]:
    """The ports a driver gave in either form: the typed form when filled, else the text.

    The text field of a released-defaulted pair holds its released default (``"any"``,
    ``""``) unless a producer set it to ``None``. *unset* is that released default's text,
    read when the text is ``None`` too; it is ``None`` when the released field was required:
    then neither form filled raises ``ValueError`` naming *record* and *field*. *parse*
    reads the text form.
    """
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
    """*rule*'s destination ports (``()`` is any port). The released ``dst_port`` was
    required, so a rule with neither form filled raises ``ValueError``."""
    return ports_of(
        rule.dst_ports, rule.dst_port, unset=None, record="FirewallRule", field="dst_port"
    )


def nat_rule_dst_ports(rule: NatRule) -> tuple[PortRange, ...]:
    """*rule*'s matched destination ports (``()`` is no port: any). A text set to ``None``
    with no typed form reads as the released default ``""``."""
    return ports_of(
        rule.dst_ports,
        rule.dst_port,
        unset="",
        record="NatRule",
        field="dst_port",
        parse=parse_nat_port_ranges,
    )


def nat_rule_translated_ports(rule: NatRule) -> tuple[PortRange, ...]:
    """*rule*'s translated ports (``()`` is no port). A text set to ``None`` with no typed
    form reads as the released default ``""``."""
    return ports_of(
        rule.translated_ports,
        rule.translated_port,
        unset="",
        record="NatRule",
        field="translated_port",
        parse=parse_nat_port_ranges,
    )


def l3_rule_src_ports(rule: L3Rule) -> tuple[PortRange, ...]:
    """*rule*'s source ports (``()`` is any port). A text set to ``None`` with no typed
    form reads as the released default ``"any"``."""
    return ports_of(rule.src_ports, rule.src_port, unset="any", record="L3Rule", field="src_port")


def l3_rule_dst_ports(rule: L3Rule) -> tuple[PortRange, ...]:
    """*rule*'s destination ports (``()`` is any port). A text set to ``None`` with no
    typed form reads as the released default ``"any"``."""
    return ports_of(rule.dst_ports, rule.dst_port, unset="any", record="L3Rule", field="dst_port")


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


# --- window size -------------------------------------------------------------------------

_SIZE = re.compile(r"\s*([0-9]+(?:\.[0-9]+)?)([kKmMgGtT]?)\s*")
_SIZE_UNITS = {"": 1, "k": 1024, "m": 1024**2, "g": 1024**3, "t": 1024**4}


def parse_window_size(text: str) -> int:
    """Return an iperf size option (``"8M"``, ``"512K"``, ``"65536"``) as a byte count.

    The grammar is iperf's: a decimal number, optionally with a fraction, and an optional
    suffix ``K``, ``M``, ``G`` or ``T`` (either case) in binary units (``K`` = 1024). A
    fractional result is truncated, as iperf does. Text that is not such a size, or that
    gives zero, raises ``ValueError``; a non-text value raises ``TypeError``.
    """
    if not isinstance(cast(object, text), str):
        raise TypeError(f"window size: takes text, not {text!r}")
    match = _SIZE.fullmatch(text)
    if match is None:
        raise ValueError(f"window size: {text!r} is not a size such as '8M'")
    number, unit = match.groups()
    size = int(Decimal(number) * _SIZE_UNITS[unit.lower()])
    if size <= 0:
        raise ValueError(f"window size: {text!r} is not a positive size")
    return size


# --- enum parameters ---------------------------------------------------------------------


class ReleasedDefault(str):
    """The released ``str`` default of an operation's parameter (``"udp"``).

    It is that text (equal to it, and shown as it by ``repr`` and ``inspect.signature``),
    and it lets :func:`coerce_enum` tell a call that left the parameter out, which must not
    warn, from a caller who passed the plain text.
    """

    __slots__ = ()


def coerce_enum[E: Enum](enum_type: type[E], value: E | str | int, *, what: str) -> E:
    """Return *value* as a member of *enum_type*, for an operation's own released ``str``
    parameter.

    A member is returned as is. A plain string naming a member's value is accepted for the
    deprecation period: it warns (``DeprecationWarning``, pointing at the operation's
    caller) and returns the member. A :class:`ReleasedDefault` (the parameter was left out)
    converts the same way with no warning. For an ``IntEnum`` the number is the value, not a
    deprecated spelling: a plain ``int`` (never a ``bool``) naming a member returns it with
    no warning. A string, or an ``IntEnum``'s ``int``, that names no member raises
    ``ValueError`` listing the legal values. A value of any other type (``None``,
    ``bytes``, a ``bool``, a ``float``, a list, or an ``int`` for an enum that is not an
    ``IntEnum``) raises ``TypeError``.
    """
    if isinstance(value, enum_type):
        return value
    given = cast(object, value)  # checked at run time too: callers are not all type-checked
    numeric = issubclass(enum_type, IntEnum)
    # True == 1 and 80.0 == 80 must not pick an IntEnum member: a bool or float is a wrong type.
    if isinstance(given, bool) or not isinstance(given, (int, str) if numeric else str):
        kinds = f"{enum_type.__name__}, int or str" if numeric else f"{enum_type.__name__} or str"
        raise TypeError(f"{what}: takes a {kinds}, not {given!r}")
    legal = [m.value for m in enum_type]
    if numeric and isinstance(given, str):  # an IntEnum's value is the number, never its text
        raise ValueError(f"{what}: {given!r} is not one of {legal}")
    try:
        member = enum_type(given)
    except ValueError:
        raise ValueError(f"{what}: {given!r} is not one of {legal}") from None
    if numeric or isinstance(given, ReleasedDefault):
        return member  # a number is an IntEnum's value; a default is not the caller's spelling
    warnings.warn(
        f"{what}: plain string {value!r} is deprecated; pass {enum_type.__name__}.{member.name}",
        DeprecationWarning,
        stacklevel=3,
    )
    return member
