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
import warnings
from collections.abc import Mapping
from enum import Enum
from pathlib import Path

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
