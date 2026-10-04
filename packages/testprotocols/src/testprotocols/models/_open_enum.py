"""Keep an open-enum field and its raw-word companion in agreement (shape 3o).

A field typed ``E`` (an enum with a catch-all member, ``OTHER``) has a companion
``<field>_raw: str | None``. The raw word is the device's own spelling, kept only
when the field is the catch-all. The two always agree, however the record is built
or changed:

- a member sets the field and clears the raw word;
- a plain string naming a member converts and warns (see
  :func:`~testprotocols.deprecation.coerce_open_enum`), clearing the raw word;
- any other string sets the field to the catch-all and the raw word to that string,
  without a warning;
- assigning the raw word to a field that is not the catch-all raises ``ValueError``,
  but at construction (where ``dataclasses.replace`` hands the old raw word back
  with a changed field) the raw word is dropped, because it belongs to the old value.

A model declares the pair, with the raw field LAST among the pair (the generated
``__init__`` assigns in field order), and routes ``__setattr__`` through it::

    _STATE = OpenEnumField(ConnState, ConnState.OTHER, "state", "state_raw")

    state: ConnState | str
    ...
    state_raw: str | None = None

    @override
    def __setattr__(self, name: str, value: object) -> None:
        if not _STATE.assign(self, name, value, "Connection"):
            super().__setattr__(name, value)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import cast

from testprotocols.deprecation import MODEL_FRAMES, coerce_open_enum


@dataclass(frozen=True)
class OpenEnumField[E: Enum]:
    """One open-enum field *field*, its catch-all *other* and its raw companion *raw_field*."""

    enum_type: type[E]
    other: E
    field: str
    raw_field: str
    casefold: bool = False

    def assign(self, obj: object, name: str, value: object, owner: str) -> bool:
        """Handle an assignment of *name* on *obj*; return ``False`` for any other name.

        The caller falls through to ``super().__setattr__`` when this returns ``False``.
        """
        state = vars(obj)
        stash = f"_{self.field}_derived"
        initial = (
            self.raw_field not in state
        )  # the generated __init__ has not reached the raw field
        if name == self.field:
            member, raw = coerce_open_enum(
                self.enum_type,
                cast("E | str", value),
                what=f"{owner}.{name}",
                other=self.other,
                casefold=self.casefold,
                skip_file_prefixes=MODEL_FRAMES,
            )
            state[name] = member
            if initial:
                state[stash] = raw  # the raw field's own assignment settles it
            else:
                state[self.raw_field] = raw
            return True
        if name != self.raw_field:
            return False
        if value is not None and not isinstance(value, str):
            raise TypeError(f"{owner}.{name} takes text or None, not {value!r}")
        member = cast(E, state[self.field])
        if initial:
            derived = cast("str | None", state.pop(stash, None))
            if derived is not None:
                value = derived  # the field was given an unknown word: that word is the raw word
            elif member is not self.other:
                value = None  # a copy's old raw word does not belong to the new value
        elif value is not None and member is not self.other:
            raise ValueError(
                f"{owner}.{name} {value!r} needs {owner}.{self.field} to be "
                f"{self.enum_type.__name__}.{self.other.name}, not {member!r}"
            )
        state[name] = value
        return True
