"""Multicast group record types and type aliases."""

from __future__ import annotations

import warnings
from collections.abc import Iterable, Sequence
from enum import Enum
from typing import NamedTuple, Self, cast


class MulticastGroupRecordType(Enum):
    """IGMPv3 group record type codes as defined in RFC 3376."""

    MODE_IS_INCLUDE = 1
    MODE_IS_EXCLUDE = 2
    CHANGE_TO_INCLUDE_MODE = 3
    CHANGE_TO_EXCLUDE_MODE = 4
    ALLOW_NEW_SOURCES = 5
    BLOCK_OLD_SOURCES = 6


McastSource = str
McastGroup = str
MulticastGroupRecord = list[tuple[list[McastSource], McastGroup, MulticastGroupRecordType]]
"""A list of (sources, group, record_type) group records (IGMPv3 / MLDv2). Each entry is a
:class:`GroupRecord`; a plain tuple is deprecated (see :func:`group_records`)."""


class _GroupRecordFields(NamedTuple):
    sources: list[McastSource]
    group: McastGroup
    record_type: MulticastGroupRecordType


class GroupRecord(_GroupRecordFields):
    """One IGMPv3 / MLDv2 group record: the *sources* (addresses as text, empty for none),
    the multicast *group* address and the *record_type*.

    A named tuple: it is the released ``(sources, group, record_type)`` tuple, so it fits the
    released :data:`MulticastGroupRecord` parameter type and a driver that unpacks the
    released tuple keeps working. *sources* is held as a new list. A value of the wrong type
    raises ``TypeError``.
    """

    __slots__ = ()

    def __new__(
        cls,
        sources: list[McastSource],
        group: McastGroup,
        record_type: MulticastGroupRecordType,
    ) -> Self:
        given = cast(object, sources)
        if not isinstance(given, list | tuple):
            raise TypeError(f"GroupRecord.sources takes a list of addresses, not {given!r}")
        held: list[str] = []
        for item in cast("Sequence[object]", given):
            if not isinstance(item, str):
                raise TypeError(f"GroupRecord.sources holds text only, not {item!r}")
            held.append(item)
        if not isinstance(cast(object, group), str):
            raise TypeError(f"GroupRecord.group takes text, not {group!r}")
        if not isinstance(cast(object, record_type), MulticastGroupRecordType):
            raise TypeError(
                f"GroupRecord.record_type takes a MulticastGroupRecordType, not {record_type!r}"
            )
        return super().__new__(cls, held, group, record_type)


def group_records(
    records: Iterable[GroupRecord | tuple[list[McastSource], McastGroup, MulticastGroupRecordType]],
    *,
    what: str,
) -> list[GroupRecord]:
    """Return *records* as :class:`GroupRecord` entries, for a driver's group-record parameter.

    A :class:`GroupRecord` passes as is. A plain ``(sources, group, record_type)`` tuple is
    deprecated: it converts, and the call warns once (``DeprecationWarning``, pointing at the
    driver's caller). Anything else raises ``TypeError``.
    """
    converted: list[GroupRecord] = []
    plain = False
    for record in records:
        item = cast(object, record)
        if isinstance(item, GroupRecord):
            converted.append(item)
            continue
        if not isinstance(item, tuple) or len(cast("tuple[object, ...]", item)) != 3:
            raise TypeError(f"{what}: takes GroupRecord entries, not {item!r}")
        sources, group, record_type = cast(
            "tuple[list[McastSource], McastGroup, MulticastGroupRecordType]", item
        )
        converted.append(GroupRecord(sources, group, record_type))
        plain = True
    if plain:
        warnings.warn(
            f"{what}: a plain (sources, group, record_type) tuple is deprecated; pass GroupRecord",
            DeprecationWarning,
            stacklevel=3,
        )
    return converted
