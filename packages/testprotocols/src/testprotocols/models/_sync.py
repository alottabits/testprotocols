"""Keep a deprecated text field and its typed successor in agreement (shape 4(ii)).

A released field holds a grammar as text; a new field holds the same value
typed. The two always agree, whichever way the record was built or changed:

- at construction, a typed value fills the text, a text fills the typed value
  (and warns), and two that disagree raise ``ValueError``;
- through ``dataclasses.replace`` and through assignment, **the side that
  changed wins**: assigning the text field re-parses it into the typed field
  (and warns), assigning the typed field formats it into the text field.

The provenance field must be the model's LAST field: ``__init__`` assigns fields in
order, and a pair field assigned after it would take the assignment path and lose a
``replace`` change silently. :func:`settle` raises ``TypeError`` otherwise.

A model declares one :class:`SyncedField` per pair and one hidden init field
(the *provenance*, ``repr=False, compare=False``) holding the agreed text of
every pair; ``replace`` copies it, which is how a changed side is told from an
unchanged one. The model then calls :func:`settle` from ``__post_init__`` and
:func:`assign` from ``__setattr__``::

    _PAIRS = (SyncedField("src_port", "src_ports", ...),)

    _seen: tuple[str, ...] | None = field(default=None, kw_only=True, repr=False, compare=False)

    def __post_init__(self) -> None:
        settle(self, _PAIRS, "_seen")

    def __setattr__(self, name: str, value: object) -> None:
        assign(self, name, value, _PAIRS, "_seen")

A text side spread over several released fields (a ``(kind, value)`` pair that
spells a tagged union) is one :class:`SyncedFields`: its text is the tuple of
those fields' values, and assigning one of them re-parses the tuple with that one
changed. A model's pairs share one text type, which types its provenance.
"""

from __future__ import annotations

import dataclasses
import warnings
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Protocol, cast

from testprotocols.deprecation import MODEL_FRAMES, coerce_enum

if TYPE_CHECKING:
    from _typeshed import DataclassInstance


def _warn(old: str, new: str, owner: str) -> None:
    warnings.warn(
        f"{owner}.{old} is deprecated; use {new}",
        DeprecationWarning,
        skip_file_prefixes=MODEL_FRAMES,
    )


class _Codec[S, T](Protocol):
    """What the agreement rule needs of a pair: the text side *S* and typed side *T*."""

    @property
    def new(self) -> str: ...
    @property
    def label(self) -> str: ...
    @property
    def parse(self) -> Callable[[S], T]: ...
    @property
    def format(self) -> Callable[[T], S]: ...
    @property
    def normalize(self) -> Callable[[T], T]: ...
    @property
    def empty_text(self) -> S: ...


def _agree[S, T](pair: _Codec[S, T], old: S, new: T, seen: S | None, owner: str) -> T:
    """The typed value a pair whose text is *old* and typed value *new* agrees on.

    *seen* is the agreed text of the record this one was copied from (``None`` at
    construction): a side that differs from it is the side that changed.
    """
    new = pair.normalize(new)
    if seen is None:  # construction
        if old == pair.empty_text:
            return new
        typed = pair.parse(old)
        if pair.format(new) == pair.empty_text:
            _warn(pair.label, pair.new, owner)
        elif typed != new:
            raise ValueError(_disagree(pair, owner, old, new))
        return typed
    # a copy of an agreed record, perhaps with a side changed
    text_changed = old != seen
    typed_changed = new != pair.parse(seen)
    if text_changed and not typed_changed:
        typed = pair.parse(old)  # a malformed text raises before it warns
        _warn(pair.label, pair.new, owner)
        return typed
    if text_changed and pair.parse(old) != new:
        raise ValueError(_disagree(pair, owner, old, new))
    return new


def _disagree[S, T](pair: _Codec[S, T], owner: str, old: S, new: T) -> str:
    return f"{owner}.{pair.label} {old!r} and {pair.new} {pair.format(new)!r} disagree"


@dataclass(frozen=True)
class SyncedField[T]:
    """One deprecated text field *old* and its typed successor *new*.

    *parse* turns text into the typed value (``ValueError`` when malformed),
    *format* is its inverse, and *empty_text* is the text default (the value of
    *old* when it was not given).
    """

    old: str
    new: str
    parse: Callable[[str], T]
    format: Callable[[T], str]
    normalize: Callable[[T], T]
    empty_text: str
    keep_text: bool = False
    """Keep a text that parses to the agreed value exactly as given, instead of
    rewriting it to ``format``'s form (for text whose released spelling has
    several equal readings, such as an ISO-8601 offset ``Z`` or ``+00:00``)."""

    @property
    def label(self) -> str:
        return self.old

    def owns(self, name: str) -> bool:
        return name in (self.old, self.new)

    def settle(self, obj: object, seen: str | None, owner: str) -> str:
        """Bring *obj*'s pair into agreement; return the agreed text."""
        given: str = getattr(obj, self.old)
        typed = _agree(self, given, getattr(obj, self.new), seen, owner)
        return self._put(obj, typed, given)

    def assign(self, obj: object, name: str, value: object, owner: str) -> str:
        """Set *name* (one of the pair) to *value* and the other side to match;
        return the agreed text. A malformed text leaves *obj* untouched."""
        if name == self.old:
            if not isinstance(value, str):
                raise TypeError(f"{owner}.{self.old} takes text, not {value!r}")
            typed = self.parse(value)
            _warn(self.old, self.new, owner)
            return self._put(obj, typed, value)
        return self._put(obj, self.normalize(cast(T, value)))

    def _put(self, obj: object, typed: T, given: str | None = None) -> str:
        text = self.format(typed)
        if self.keep_text and given and self.parse(given) == typed:
            text = given
        object.__setattr__(obj, self.old, text)
        object.__setattr__(obj, self.new, typed)
        return text


@dataclass(frozen=True)
class SyncedFields[S: tuple[object, ...], T]:
    """Deprecated fields *old* that together spell what one typed field *new* holds.

    The text side is the tuple of the *old* fields' values, in order (for example a
    ``(kind, value)`` pair spelling a tagged union). *kinds* gives each old field's
    type: a plain string assigned to an enum-typed field is converted with
    :func:`~testprotocols.deprecation.coerce_enum` (it warns; an unknown one raises
    ``ValueError`` listing the legal values), any other value of another type raises ``TypeError``,
    else the whole tuple is re-parsed with that one replaced. Otherwise as :class:`SyncedField`.
    """

    old: tuple[str, ...]
    kinds: tuple[type, ...]
    new: str
    parse: Callable[[S], T]
    format: Callable[[T], S]
    normalize: Callable[[T], T]
    empty_text: S

    @property
    def label(self) -> str:
        return "/".join(self.old)

    def owns(self, name: str) -> bool:
        return name == self.new or name in self.old

    def settle(self, obj: object, seen: S | None, owner: str) -> S:
        """Bring *obj*'s fields into agreement; return the agreed text tuple."""
        return self._put(obj, _agree(self, self._text(obj), getattr(obj, self.new), seen, owner))

    def assign(self, obj: object, name: str, value: object, owner: str) -> S:
        """Set *name* to *value* and the other side to match; return the agreed text
        tuple. A malformed text leaves *obj* untouched."""
        if name in self.old:
            kind = self.kinds[self.old.index(name)]
            if issubclass(kind, Enum) and isinstance(value, str):
                # a plain string warns; an unknown one raises ValueError listing the legal values
                value = coerce_enum(
                    kind, value, what=f"{owner}.{name}", skip_file_prefixes=MODEL_FRAMES
                )
            if not isinstance(value, kind):
                raise TypeError(f"{owner}.{name} takes {kind.__name__}, not {value!r}")
            typed = self.parse(self._text(obj, {name: value}))
            _warn(self.label, self.new, owner)
        else:
            typed = self.normalize(cast(T, value))
        return self._put(obj, typed)

    def _text(self, obj: object, changed: dict[str, object] | None = None) -> S:
        given = changed or {}
        return cast(S, tuple(given[n] if n in given else getattr(obj, n) for n in self.old))

    def _put(self, obj: object, typed: T) -> S:
        text = self.format(typed)
        for name, part in zip(self.old, text, strict=True):
            object.__setattr__(obj, name, part)
        object.__setattr__(obj, self.new, typed)
        return text


class Settler[S](Protocol):
    """What :func:`settle` and :func:`assign` need of a pair whose agreed text is *S*
    (a ``SyncedField`` is a ``Settler[str]``)."""

    def owns(self, name: str) -> bool: ...
    def settle(self, obj: object, seen: S | None, owner: str) -> S: ...
    def assign(self, obj: object, name: str, value: object, owner: str) -> S: ...


def settle[S](obj: object, pairs: Sequence[Settler[S]], seen_attr: str) -> None:
    """Call from ``__post_init__``: agree every pair and record the agreed texts."""
    owner = type(obj).__name__
    if "__dataclass_fields__" not in vars(type(obj)):
        # an undecorated subclass inherits its parent's fields and would silently drop its own
        raise TypeError(f"{owner}: a subclass of a synced model must be decorated with @dataclass")
    # fields() lists real fields only: ClassVar and InitVar pseudo-fields are excluded
    if dataclasses.fields(cast("DataclassInstance", obj))[-1].name != seen_attr:
        raise TypeError(f"{owner}: the provenance field {seen_attr!r} must be its last field")
    seen: tuple[S, ...] | None = getattr(obj, seen_attr)
    agreed = tuple(
        pair.settle(obj, None if seen is None else seen[i], owner) for i, pair in enumerate(pairs)
    )
    object.__setattr__(obj, seen_attr, agreed)


def assign[S](
    obj: object, name: str, value: object, pairs: Sequence[Settler[S]], seen_attr: str
) -> None:
    """Call from ``__setattr__``: set *name*, re-syncing its pair once *obj* is settled."""
    seen: tuple[S, ...] | None = obj.__dict__.get(seen_attr)
    if seen is not None:
        for i, pair in enumerate(pairs):
            if pair.owns(name):
                text = pair.assign(obj, name, value, type(obj).__name__)
                object.__setattr__(obj, seen_attr, (*seen[:i], text, *seen[i + 1 :]))
                return
    object.__setattr__(obj, name, value)
