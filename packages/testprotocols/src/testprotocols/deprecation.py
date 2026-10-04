"""Deprecation helpers for renamed public symbols.

A removal, rename or retype is preceded by a deprecation period in which both
forms work and the old one emits ``DeprecationWarning`` (CONTRIBUTING.md,
"Versioning"). A renamed class or model keeps its old name through a module
``__getattr__`` that calls :func:`renamed_attribute`. A renamed protocol method
is declared under both names; a driver implements the new one and lets the old
one delegate, calling :func:`warn_renamed` first.
"""

from __future__ import annotations

import dataclasses
import re
import warnings
from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from typing import cast

MODEL_FRAMES = (str(Path(__file__).parent / "models"), "<string>", dataclasses.__file__)
"""The *skip_file_prefixes* of a warning raised inside a model's ``__post_init__`` or
``__setattr__``: the models package, the dataclass-generated ``__init__`` (filename
``<string>``) and ``dataclasses.replace``. The warning then points at the first frame
outside them, the caller's construction or assignment site."""


def renamed_attribute(
    module: str, name: str, renames: Mapping[str, str], namespace: Mapping[str, object]
) -> object:
    """Resolve a deprecated module attribute *name* to its new object.

    Call from a module-level ``__getattr__``: *renames* maps old names to new
    ones and *namespace* is the module's ``globals()``. Names not in *renames*
    raise ``AttributeError`` as a normal missing attribute would.
    """
    new = renames.get(name)
    if new is None:
        raise AttributeError(f"module {module!r} has no attribute {name!r}")
    warnings.warn(f"{module}.{name} is deprecated; use {new}", DeprecationWarning, stacklevel=3)
    return namespace[new]


def warn_renamed(old: str, new: str) -> None:
    """Warn that the protocol member *old* is deprecated in favour of *new*.

    For a driver's old-name method during the deprecation period::

        def old_name(self, value: str) -> None:
            warn_renamed("old_name", "new_name")
            self.new_name(value)
    """
    warnings.warn(f"{old} is deprecated; use {new}", DeprecationWarning, stacklevel=3)


def coerce_enum[E: Enum](
    enum_type: type[E],
    value: E | str,
    *,
    what: str,
    skip_file_prefixes: tuple[str, ...] = (),
) -> E:
    """Return *value* as a member of *enum_type*.

    A member is returned as is. A plain string naming a member's value is
    accepted for the deprecation period: it warns and returns the member.
    Any other value raises ``ValueError`` listing the legal values.

    The warning points at the caller's caller (``stacklevel=3``), which is the
    right frame for a driver method that coerces at its boundary. Called from
    a model's ``__post_init__`` or ``__setattr__`` that frame would be the
    dataclass-generated ``__init__``: pass *skip_file_prefixes* (for a model in
    this package, :data:`MODEL_FRAMES`) and the warning points at the first
    frame outside them, the user's construction site.
    """
    if isinstance(value, enum_type):
        return value
    try:
        member = enum_type(value)
    except ValueError:
        legal = [m.value for m in enum_type]
        raise ValueError(f"{what}: {value!r} is not one of {legal}") from None
    warnings.warn(
        f"{what}: plain string {value!r} is deprecated; pass {enum_type.__name__}.{member.name}",
        DeprecationWarning,
        stacklevel=2 if skip_file_prefixes else 3,
        skip_file_prefixes=skip_file_prefixes,
    )
    return member


def coerce_open_enum[E: Enum](
    enum_type: type[E],
    value: E | str,
    *,
    what: str,
    other: E,
    skip_file_prefixes: tuple[str, ...] = (),
) -> tuple[E, str | None]:
    """Return *value* as ``(member, raw)`` for an open enum (shape 3o).

    The set is open by contract: a device may report a word the enum does not
    list, so an unknown word is data, not an error. *other* is the enum's
    catch-all member (``OTHER``).

    - A member is returned as is, with raw ``None``.
    - A plain string naming a member's value converts, warns as :func:`coerce_enum`
      does, and gives raw ``None``. The match is exact, including letter case.
    - Any other string gives ``(other, value)`` and does not warn: the raw word
      is kept so nothing is lost or guessed.
    - Any other type raises ``TypeError``.

    The warning frame works as in :func:`coerce_enum`.
    """
    given = cast(object, value)  # checked at run time too: callers are not all type-checked
    if isinstance(given, enum_type):
        return given, None
    if not isinstance(given, str):
        raise TypeError(f"{what}: takes a {enum_type.__name__} or str, not {given!r}")
    text: str = given
    for member in enum_type:
        if member.value == text:
            warnings.warn(
                f"{what}: plain string {text!r} is deprecated; "
                f"pass {enum_type.__name__}.{member.name}",
                DeprecationWarning,
                stacklevel=2 if skip_file_prefixes else 3,
                skip_file_prefixes=skip_file_prefixes,
            )
            return member, None
    return other, text


_DECIMAL = re.compile(r"[+-]?[0-9]+")


def coerce_int(
    value: int | str,
    *,
    what: str,
    skip_file_prefixes: tuple[str, ...] = (),
) -> int:
    """Return *value* as an ``int``.

    An ``int`` (not a ``bool``) is returned unchanged. A string of optionally signed
    decimal digits (``"443"``, ``"-1"``, ``"+5"``) is accepted for the deprecation
    period: it warns and returns the number. Text that is not a decimal integer
    raises ``ValueError`` naming *what* and the value; any other type (``bool``,
    ``float``, ``None``, ``bytes``) raises ``TypeError``.

    The warning frame works as in :func:`coerce_enum`: ``stacklevel=3`` for a driver
    method that coerces at its boundary, or the first frame outside
    *skip_file_prefixes* for a model.
    """
    given = cast(object, value)  # checked at run time too: callers are not all type-checked
    if isinstance(given, bool) or not isinstance(given, (int, str)):
        raise TypeError(f"{what}: takes an int, not {given!r}")
    if isinstance(given, int):
        return given
    value = given
    if not _DECIMAL.fullmatch(value):
        raise ValueError(f"{what}: {value!r} is not a decimal integer")
    number = int(value)
    warnings.warn(
        f"{what}: plain string {value!r} is deprecated; pass the int {number}",
        DeprecationWarning,
        stacklevel=2 if skip_file_prefixes else 3,
        skip_file_prefixes=skip_file_prefixes,
    )
    return number
