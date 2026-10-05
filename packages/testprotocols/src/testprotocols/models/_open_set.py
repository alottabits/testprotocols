"""Keep a multi-valued open set and its released word list in agreement (shape 3o, many words).

A released field holds the device's words as ``list[str]``. The set is open: a device
may report a word the enum does not name, and one record may carry several. The pair
therefore splits the word list in two new fields, with no per-element catch-all:

- *known*: ``tuple[E, ...]``, the words that name a member of *enum_type*;
- *unknown*: ``tuple[str, ...]``, the words that name none, verbatim and in order.

The released list (*old*) keeps the device's full word list, in its own order and with
its own repeats, so nothing is lost or guessed. The agreed value of the set is that
list as a tuple (the *provenance* text, ``tuple[str, ...]``): ``split`` of it is the
typed pair, and the typed pair formats back to it (known words first, then unknown).
A word matches a member exactly, letter case included, as ``coerce_open_enum`` does.

The rule, for construction, ``dataclasses.replace`` and assignment alike, is the one
of :mod:`testprotocols.models._sync`: **the side that changed wins**.

- At construction a typed pair fills the word list silently; a word list alone
  splits into the pair and warns (the list is deprecated); both given and not
  agreeing raise ``ValueError``.
- Through ``replace`` and assignment, changing the typed side rewrites the word list
  silently (kept as it is when it already splits into the new pair, so the device's
  order survives); changing the word list re-splits the pair and warns; both changed
  and not agreeing raise ``ValueError``.
- Everything is validated before anything is stored: a refused assignment changes
  nothing. A list given as the word list, or a ``tuple`` or ``list`` given as a typed
  side, is accepted; a bare ``str`` is a ``TypeError`` (it would be read as letters), as is
  a non-text word or a non-member in *known*; an *unknown* word that names a member
  is a ``ValueError`` (it belongs in *known*, and would not survive a round trip).
- The word list is a mutable ``list``, as released. Changing it in place is not seen
  at once; it is noticed by the next ``replace``, and an assignment replaces it.

Like :class:`~testprotocols.models._open_enum.OpenEnumPair` it is a ``Settler`` of
:mod:`testprotocols.models._sync`: a model declares the pair, the hidden provenance
field LAST, and calls ``settle`` from ``__post_init__`` and ``assign`` from
``__setattr__``.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import cast

from testprotocols.deprecation import MODEL_FRAMES, warn_at_caller

type Words = tuple[str, ...]


@dataclass(frozen=True)
class OpenSetPair[E: Enum]:
    """The word list *old*, the member tuple *known* and the leftover words *unknown*."""

    enum_type: type[E]
    old: str
    known: str
    unknown: str

    def owns(self, name: str) -> bool:
        return name in (self.old, self.known, self.unknown)

    # --- the codec ---

    def split(self, words: Words) -> tuple[tuple[E, ...], Words]:
        """The members and the unnamed words in *words*, each in order."""
        by_value = {str(member.value): member for member in self.enum_type}
        known = tuple(by_value[w] for w in words if w in by_value)
        return known, tuple(w for w in words if w not in by_value)

    def format(self, known: tuple[E, ...], unknown: Words) -> Words:
        """The word list a typed pair writes: the members' values, then the unnamed words."""
        return (*(str(member.value) for member in known), *unknown)

    # --- validation ---

    def _words(self, value: object, owner: str) -> Words:
        if isinstance(value, str) or not isinstance(value, Iterable):
            raise TypeError(f"{owner}.{self.old} takes a list of text, not {value!r}")
        words = tuple(cast("Iterable[object]", value))
        for word in words:
            if not isinstance(word, str):
                raise TypeError(f"{owner}.{self.old} holds text only, not {word!r}")
        return cast(Words, words)

    def _known(self, value: object, owner: str) -> tuple[E, ...]:
        if isinstance(value, str) or not isinstance(value, Iterable):
            raise TypeError(
                f"{owner}.{self.known} takes a tuple of {self.enum_type.__name__}, not {value!r}"
            )
        members = tuple(cast("Iterable[object]", value))
        for member in members:
            if not isinstance(member, self.enum_type):
                raise TypeError(
                    f"{owner}.{self.known} holds {self.enum_type.__name__} members only, "
                    f"not {member!r}; a device word that names none belongs in {self.unknown}"
                )
        return cast("tuple[E, ...]", members)

    def _unknown(self, value: object, owner: str) -> Words:
        if isinstance(value, str) or not isinstance(value, Iterable):
            raise TypeError(f"{owner}.{self.unknown} takes a tuple of text, not {value!r}")
        words = tuple(cast("Iterable[object]", value))
        for word in words:
            if not isinstance(word, str):
                raise TypeError(f"{owner}.{self.unknown} holds text only, not {word!r}")
        known, _ = self.split(cast(Words, words))
        if known:
            raise ValueError(
                f"{owner}.{self.unknown} holds {known[0].value!r}, which names a "
                f"{self.enum_type.__name__}: it belongs in {self.known}"
            )
        return cast(Words, words)

    # --- the agreement rule ---

    def settle(self, obj: object, seen: Words | None, owner: str) -> Words:
        """Bring *obj*'s three fields into agreement; return the agreed word list."""
        words = self._words(getattr(obj, self.old), owner)
        known = self._known(getattr(obj, self.known), owner)
        unknown = self._unknown(getattr(obj, self.unknown), owner)
        typed = (known, unknown)
        if seen is None:  # construction
            if not words:
                return self._put(obj, self.format(*typed), typed)
            if not known and not unknown:
                parsed = self.split(words)
                self._warn(owner)
                return self._put(obj, words, parsed)
            return self._put(obj, self._agreed(owner, words, typed), typed)
        text_changed = words != seen
        typed_changed = typed != self.split(seen)
        if text_changed and not typed_changed:
            parsed = self.split(words)
            self._warn(owner)
            return self._put(obj, words, parsed)
        if text_changed:
            return self._put(obj, self._agreed(owner, words, typed), typed)
        if typed_changed:
            return self._put(obj, self.format(*typed), typed)
        return self._put(obj, seen, typed)

    def assign(self, obj: object, name: str, value: object, owner: str) -> Words:
        """Set *name* (one of the three) to *value* and the rest to match; return the
        agreed word list. A refused value leaves *obj* untouched."""
        if name == self.old:
            words = self._words(value, owner)
            typed = self.split(words)
            self._warn(owner)
            return self._put(obj, words, typed)
        known: tuple[E, ...] = getattr(obj, self.known)
        unknown: Words = getattr(obj, self.unknown)
        if name == self.known:
            known = self._known(value, owner)
        else:
            unknown = self._unknown(value, owner)
        current = self._words(getattr(obj, self.old), owner)
        words = current if self.split(current) == (known, unknown) else self.format(known, unknown)
        return self._put(obj, words, (known, unknown))

    def _agreed(self, owner: str, words: Words, typed: tuple[tuple[E, ...], Words]) -> Words:
        if self.split(words) != typed:
            raise ValueError(
                f"{owner}.{self.old} {list(words)!r} and {self.known}/{self.unknown} "
                f"{typed!r} disagree"
            )
        return words

    def _warn(self, owner: str) -> None:
        warn_at_caller(
            f"{owner}.{self.old} is deprecated; use {self.known} and {self.unknown}",
            skip_file_prefixes=MODEL_FRAMES,
        )

    def _put(self, obj: object, words: Words, typed: tuple[tuple[E, ...], Words]) -> Words:
        object.__setattr__(obj, self.old, list(words))
        object.__setattr__(obj, self.known, typed[0])
        object.__setattr__(obj, self.unknown, typed[1])
        return words
