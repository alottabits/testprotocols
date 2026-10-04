"""Layer-4 port ranges and the released string grammar they replace.

The released ACL records carried ports as text (``"any"``, ``"80"``,
``"80-90"``, ``"22,80-90"``). :class:`PortRange` is the typed form;
:func:`parse_port_ranges` and :func:`format_port_ranges` convert to and from
the released text and are exact inverses on canonical text.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import cast, override

_MAX_PORT = 65535


@dataclass(frozen=True)
class PortRange:
    """An inclusive L4 port range; a single port has ``first == last``.

    ``1 <= first <= last <= 65535``, else ``ValueError``; a non-int (a bool, a
    float) raises ``TypeError``.
    """

    first: int
    last: int

    def __post_init__(self) -> None:
        for name, value in (("first", self.first), ("last", self.last)):
            if type(value) is not int:  # not a bool, a float or an int subclass
                raise TypeError(f"PortRange.{name} must be an int, not {type(value).__name__}")
            if not 1 <= value <= _MAX_PORT:
                raise ValueError(f"PortRange.{name} {value} is outside 1-{_MAX_PORT}")
        if self.first > self.last:
            raise ValueError(f"PortRange {self.first}-{self.last}: first is above last")

    @classmethod
    def single(cls, port: int) -> PortRange:
        """The range holding exactly *port*."""
        return cls(port, port)

    @override
    def __str__(self) -> str:
        return str(self.first) if self.first == self.last else f"{self.first}-{self.last}"


def _number(text: str) -> int:
    if not (text.isascii() and text.isdigit()):
        raise ValueError(f"{text!r} is not a port number")
    return int(text)


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
            low = _number(first)
            ranges.append(PortRange(low, _number(last) if dash else low))
        except ValueError as bad:
            raise ValueError(f"malformed port spec {text!r}: {bad}") from None
    return tuple(ranges)


def format_port_ranges(ranges: tuple[PortRange, ...]) -> str:
    """The released text of *ranges*; ``()`` gives ``"any"``."""
    return ",".join(str(r) for r in ranges) if ranges else "any"


def port_tuple(value: object) -> tuple[PortRange, ...]:
    """*value* as a tuple of :class:`PortRange`: the one check on a typed port field.

    A list is converted to a tuple. A string or bytes (the released text passed to
    the typed field by mistake), another non-iterable, or an item that is not a
    ``PortRange`` (a bare port number) raises ``TypeError``.
    """
    if isinstance(value, str | bytes) or not isinstance(value, Iterable):
        raise TypeError(f"port ranges take a tuple of PortRange, not {value!r}")
    ranges: list[PortRange] = []
    for item in cast("Iterable[object]", value):
        if not isinstance(item, PortRange):
            raise TypeError(f"port ranges take a tuple of PortRange, not {item!r}")
        ranges.append(item)
    return tuple(ranges)
