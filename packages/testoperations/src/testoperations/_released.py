"""Keep a released dict return readable while the operation returns a record.

An operation that returned a ``dict`` and now returns a frozen dataclass gives its callers a
deprecation period: indexing, ``get``, ``in``, ``keys``, ``dict(result)`` and ``**result``,
``==`` against the released dict and :meth:`as_dict` all still work, each with a
``DeprecationWarning``; reading the record's fields never warns. The removal step deletes the
mixin from the record.
"""

from __future__ import annotations

import warnings
from collections.abc import Iterator, Mapping
from dataclasses import fields
from typing import override


class ReleasedMapping:
    """Mixin for a dataclass that replaces a released ``dict[str, object]`` return.

    Use it as ``@dataclass(frozen=True, eq=False)``: this class supplies the equality and the
    hash (by field, as a dataclass would), and a ``Mapping`` compares equal to the record when
    it equals the released dict. A subclass implements :meth:`_released`.
    """

    def _released(self) -> dict[str, object]:
        """The released dict this record replaces."""
        raise NotImplementedError

    def _warn(self, use: str) -> None:
        warnings.warn(
            f"{use} on {type(self).__name__} is deprecated; read the record's fields",
            DeprecationWarning,
            stacklevel=3,
        )

    def as_dict(self) -> dict[str, object]:
        """Deprecated: the released dict, with the released keys. Read the fields instead."""
        self._warn("as_dict()")
        return self._released()

    def __getitem__(self, key: str) -> object:
        self._warn("indexing")
        return self._released()[key]

    def get(self, key: str, default: object = None) -> object:
        """Deprecated: the released dict's ``get``."""
        self._warn("get()")
        return self._released().get(key, default)

    def keys(self) -> list[str]:
        """Deprecated: the released dict's keys (what ``dict(record)`` and ``**record`` read)."""
        self._warn("keys()")
        return list(self._released())

    def __iter__(self) -> Iterator[str]:
        self._warn("iteration")
        return iter(list(self._released()))

    def __contains__(self, key: object) -> bool:
        self._warn("`in`")
        return key in self._released()

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Mapping):
            self._warn("comparison with a dict")
            return self._released() == dict(other)  # pyright: ignore[reportUnknownArgumentType]
        if type(other) is not type(self):
            return NotImplemented
        return all(getattr(self, f.name) == getattr(other, f.name) for f in fields(self))  # type: ignore[arg-type]

    @override
    def __hash__(self) -> int:
        return hash(tuple(getattr(self, f.name) for f in fields(self)))  # type: ignore[arg-type]
