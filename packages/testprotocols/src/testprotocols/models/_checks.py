"""Field checks shared by the frozen records of this package.

Each check raises ``TypeError`` for a value of the wrong type and ``ValueError`` for a value of
the right type that is out of range, naming the record and the field. A ``bool`` is never taken
for a number. Not public API.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import cast


def count(owner: str, name: str, value: object) -> None:
    """A non-negative ``int``."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{owner}.{name} takes an int, not {value!r}")
    if value < 0:
        raise ValueError(f"{owner}.{name} cannot be negative: {value}")


def optional_count(owner: str, name: str, value: object) -> None:
    """A non-negative ``int`` or ``None``."""
    if value is not None:
        count(owner, name, value)


def number(owner: str, name: str, value: object, *, high: float | None = None) -> None:
    """A non-negative ``int`` or ``float`` (at most *high* when given)."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"{owner}.{name} takes a number, not {value!r}")
    if value < 0 or (high is not None and value > high):
        bound = f"0 to {high}" if high is not None else "0 or more"
        raise ValueError(f"{owner}.{name} must be {bound}: {value}")


def optional_number(owner: str, name: str, value: object, *, high: float | None = None) -> None:
    """A non-negative number or ``None``."""
    if value is not None:
        number(owner, name, value, high=high)


def flag(owner: str, name: str, value: object) -> None:
    """A ``bool``."""
    if not isinstance(value, bool):
        raise TypeError(f"{owner}.{name} takes a bool, not {value!r}")


def text(owner: str, name: str, value: object) -> None:
    """A ``str``."""
    if not isinstance(value, str):
        raise TypeError(f"{owner}.{name} takes text, not {value!r}")


def optional_text(owner: str, name: str, value: object) -> None:
    """A ``str`` or ``None``."""
    if value is not None:
        text(owner, name, value)


def when(owner: str, name: str, value: object) -> None:
    """A ``datetime``."""
    if not isinstance(value, datetime):
        raise TypeError(f"{owner}.{name} takes a datetime, not {value!r}")


def texts(owner: str, name: str, value: object) -> tuple[str, ...]:
    """A list or tuple of ``str``, returned as a tuple (a single ``str`` is refused)."""
    if not isinstance(value, list | tuple):
        raise TypeError(f"{owner}.{name} takes a tuple of text, not {value!r}")
    held: list[str] = []
    for item in cast("Iterable[object]", value):
        if not isinstance(item, str):
            raise TypeError(f"{owner}.{name} holds text only, not {item!r}")
        held.append(item)
    return tuple(held)
