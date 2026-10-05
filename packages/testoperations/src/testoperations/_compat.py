"""Internal transition helpers of the operations.

:func:`coerce_enum` converts an operation's own released string parameter to its enum
(:class:`ReleasedDefault` marks a left-out parameter), and :func:`parse_window_size` reads
the released iperf window text for the renamed iperf member. The readers of a record's
text/typed field pair are public: :mod:`testoperations.pairs`.
"""

from __future__ import annotations

import re
import warnings
from decimal import Decimal
from enum import Enum, IntEnum
from typing import cast

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
