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
import sys
import warnings
from collections.abc import Mapping
from enum import Enum, IntEnum
from pathlib import Path
from types import CodeType
from typing import cast

MODEL_FRAMES = (str(Path(__file__).parent / "models"),)
"""The *skip_file_prefixes* of a warning raised inside a model's ``__post_init__`` or
``__setattr__``: the models package. :func:`warn_at_caller` also skips ``dataclasses``
(``replace``) and the dataclass-generated ``__init__``, so the warning points at the
caller's construction, ``replace`` or assignment site."""


_ALWAYS_SKIPPED = frozenset({__file__, dataclasses.__file__})


def _generated(code: CodeType) -> bool:
    """Whether *code* is a method that ``dataclasses`` generated with ``exec``."""
    return code.co_filename == "<string>" and code.co_qualname.startswith("__create_fn__.")


def warn_at_caller(
    message: str, *, skip_file_prefixes: tuple[str, ...] = (), callers: int = 0
) -> None:
    """Emit a ``DeprecationWarning`` that points at the caller's frame.

    The frame is found by walking the stack from here, skipping:

    - every frame of this module and of ``dataclasses`` (``replace``);
    - every frame whose file name starts with one of *skip_file_prefixes*;
    - every method that ``dataclasses`` generated (the ``__init__`` of a
      dataclass, whose file name is ``<string>``);

    and then *callers* further frames. A model passes :data:`MODEL_FRAMES` and
    ``callers=0``, so the warning names the construction, ``replace`` or
    assignment site. A function that checks its own caller's argument at a
    boundary passes ``callers=1``, so the warning names that function's caller.

    The walk computes an explicit ``stacklevel``, so the result is the same on
    every supported Python version. ``warnings.warn(skip_file_prefixes=…)``
    alone does not skip the generated ``__init__`` on Python 3.12.
    """
    frame = sys._getframe(0)  # pyright: ignore[reportPrivateUsage]
    level = 1
    while frame.f_back is not None and (
        frame.f_code.co_filename in _ALWAYS_SKIPPED
        or frame.f_code.co_filename.startswith(skip_file_prefixes)
        or _generated(frame.f_code)
    ):
        frame = frame.f_back
        level += 1
    warnings.warn(message, DeprecationWarning, stacklevel=level + callers)


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


def deprecated_attribute(
    module: str, name: str, reason: str, namespace: Mapping[str, object]
) -> object:
    """Resolve a deprecated module attribute *name* that has no successor.

    Call from a module-level ``__getattr__``, as :func:`renamed_attribute` does
    for a rename: *namespace* maps the deprecated names to their objects (not the
    module's ``globals()``: the module deletes the names at run time, under
    ``if not TYPE_CHECKING:``, so that every runtime access reaches
    ``__getattr__`` and warns, while type checkers still see the definitions).
    The warning reads ``{module}.{name} is deprecated; {reason}``. A name not in
    *namespace* raises ``AttributeError`` as a normal missing attribute would.
    """
    try:
        obj = namespace[name]
    except KeyError:
        raise AttributeError(f"module {module!r} has no attribute {name!r}") from None
    warnings.warn(f"{module}.{name} is deprecated; {reason}", DeprecationWarning, stacklevel=3)
    return obj


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
    value: E | str | int,
    *,
    what: str,
    skip_file_prefixes: tuple[str, ...] = (),
) -> E:
    """Return *value* as a member of *enum_type*.

    A member is returned as is. A plain string naming a member's value is
    accepted for the deprecation period: it warns and returns the member.
    For an ``IntEnum`` the number is the value, not a deprecated spelling: a plain
    ``int`` (never a ``bool``) naming a member returns it with no warning, so a
    parameter typed ``ChannelWidth | int`` keeps accepting ``80``.
    A string, or an ``IntEnum``'s ``int``, that names no member raises
    ``ValueError`` listing the legal values. A value of any other type (``None``,
    ``bytes``, a ``bool``, a ``float``, a list, or an ``int`` for an enum that is
    not an ``IntEnum``) raises ``TypeError``.

    The warning points at the caller's caller, which is the right frame for a
    driver method that coerces at its boundary. Called from a model's
    ``__post_init__`` or ``__setattr__`` that frame would be the model's own
    code: pass *skip_file_prefixes* (for a model in this package,
    :data:`MODEL_FRAMES`) and the warning points at the first frame outside
    them and outside the dataclass-generated ``__init__``, the user's
    construction site (see :func:`warn_at_caller`).
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
    if numeric:
        return member  # a number is an IntEnum's value, not a deprecated spelling
    warn_at_caller(
        f"{what}: plain string {value!r} is deprecated; pass {enum_type.__name__}.{member.name}",
        skip_file_prefixes=skip_file_prefixes,
        callers=0 if skip_file_prefixes else 1,
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
            warn_at_caller(
                f"{what}: plain string {text!r} is deprecated; "
                f"pass {enum_type.__name__}.{member.name}",
                skip_file_prefixes=skip_file_prefixes,
                callers=0 if skip_file_prefixes else 1,
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

    The warning frame works as in :func:`coerce_enum`: the caller's caller for a
    driver method that coerces at its boundary, or the first frame outside
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
    warn_at_caller(
        f"{what}: plain string {value!r} is deprecated; pass the int {number}",
        skip_file_prefixes=skip_file_prefixes,
        callers=0 if skip_file_prefixes else 1,
    )
    return number
