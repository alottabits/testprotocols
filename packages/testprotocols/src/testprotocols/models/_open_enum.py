"""Keep an open-enum field and its raw-word companion in agreement (shape 3o).

A field typed ``E`` (an enum with a catch-all member, ``OTHER``) has a companion
``<field>_raw: str | None``: the device's own spelling, held only while the field
is the catch-all. The pair is one :class:`OpenEnumPair`, a ``Settler`` of
:mod:`testprotocols.models._sync`, so it is driven by the same ``settle`` and
``assign`` and keeps the same hidden provenance field as every synced pair. The
agreed value of the pair is ``(member, raw)``.

The rule, for construction, ``dataclasses.replace`` and assignment alike:

- a member sets the field and clears the raw word; a plain string naming a member
  converts and warns (``coerce_open_enum``) and clears it too;
- any other string, the empty one included, sets the field to the catch-all and the
  raw word to that string, kept verbatim, without a warning: the set is open;
- a raw word given with a named (non-catch-all) field raises ``ValueError``, and so
  does a raw word that disagrees with the unknown word the field was given;
- **the side that changed wins**: under ``replace`` and assignment, changing the
  field drops the old raw word (it belonged to the old value) unless a new one is
  given with it, and changing only the raw word keeps the field. Changing the raw
  word while the field is a named member raises ``ValueError``.

Everything is validated before anything is stored, so a refused assignment leaves
the record unchanged. A model declares one pair, the hidden provenance field LAST,
and calls ``settle`` from ``__post_init__`` and ``assign`` from ``__setattr__``::

    _PAIRS = (OpenEnumPair(ConnState, ConnState.OTHER, "state", "state_raw"),)

    state_raw: str | None = None
    _seen: tuple[tuple[ConnState, str | None], ...] | None = field(
        default=None, kw_only=True, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        settle(self, _PAIRS, "_seen")

    def __setattr__(self, name: str, value: object) -> None:  # a mutable model only
        assign(self, name, value, _PAIRS, "_seen")

A frozen model omits ``__setattr__``: ``__post_init__`` alone settles it, writing
through ``object.__setattr__`` (as ``settle`` does), and ``dataclasses.replace``
runs the same ``__post_init__`` with the old provenance.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import cast

from testprotocols.deprecation import MODEL_FRAMES, coerce_open_enum


@dataclass(frozen=True)
class OpenEnumPair[E: Enum]:
    """One open-enum field *field*, its catch-all *other* and its raw companion *raw_field*."""

    enum_type: type[E]
    other: E
    field: str
    raw_field: str

    def owns(self, name: str) -> bool:
        return name in (self.field, self.raw_field)

    def settle(
        self, obj: object, seen: tuple[E, str | None] | None, owner: str
    ) -> tuple[E, str | None]:
        """Bring *obj*'s pair into agreement; return the agreed ``(member, raw)``."""
        state = cast("E | str", getattr(obj, self.field))
        raw = self._raw(getattr(obj, self.raw_field), owner)
        if seen is None:  # construction: both sides are as the caller gave them
            agreed = self._resolve(state, raw, owner)
        else:  # a copy of an agreed record, perhaps with a side changed
            seen_member, seen_raw = seen
            state_changed = state is not seen_member
            raw_changed = raw != seen_raw
            if state_changed and raw_changed:
                agreed = self._resolve(state, raw, owner)
            elif state_changed:
                agreed = self._resolve(state, None, owner)  # the old raw word is the old value's
            elif raw_changed:
                agreed = self._resolve(seen_member, raw, owner)
            else:
                agreed = seen
        return self._put(obj, agreed)

    def assign(self, obj: object, name: str, value: object, owner: str) -> tuple[E, str | None]:
        """Set *name* (one of the pair) to *value* and the other side to match; return the
        agreed ``(member, raw)``. A refused value leaves *obj* untouched."""
        if name == self.field:
            agreed = self._resolve(cast("E | str", value), None, owner)
        else:
            member = cast(E, getattr(obj, self.field))
            agreed = self._resolve(member, self._raw(value, owner), owner)
        return self._put(obj, agreed)

    def _raw(self, value: object, owner: str) -> str | None:
        if value is not None and not isinstance(value, str):
            raise TypeError(f"{owner}.{self.raw_field} takes text or None, not {value!r}")
        return value

    def _resolve(self, state: E | str, raw: str | None, owner: str) -> tuple[E, str | None]:
        member, word = coerce_open_enum(
            self.enum_type,
            state,
            what=f"{owner}.{self.field}",
            other=self.other,
            skip_file_prefixes=MODEL_FRAMES,
        )
        if word is not None:  # the field was given a word that names no member
            if raw is not None and raw != word:
                raise ValueError(
                    f"{owner}.{self.field} {word!r} and {owner}.{self.raw_field} {raw!r} disagree"
                )
            return member, word
        if raw is not None and member is not self.other:
            raise ValueError(
                f"{owner}.{self.raw_field} {raw!r} needs {owner}.{self.field} to be "
                f"{self.enum_type.__name__}.{self.other.name}, not {member!r}"
            )
        return member, raw

    def _put(self, obj: object, agreed: tuple[E, str | None]) -> tuple[E, str | None]:
        object.__setattr__(obj, self.field, agreed[0])
        object.__setattr__(obj, self.raw_field, agreed[1])
        return agreed
