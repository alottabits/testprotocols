"""Multicast group record types and type aliases."""

from __future__ import annotations

from enum import Enum
from typing import NamedTuple


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
:class:`GroupRecord`.

Deprecated: a plain tuple record; see ``MulticastClient.send_mldv2_report``."""


class _GroupRecordFields(NamedTuple):
    sources: list[McastSource]
    group: McastGroup
    record_type: MulticastGroupRecordType


class GroupRecord(_GroupRecordFields):
    """One IGMPv3 / MLDv2 group record: the *sources* (addresses as text, empty for none),
    the multicast *group* address and the *record_type*.

    A named tuple: it is the released ``(sources, group, record_type)`` tuple, so a driver
    that unpacks the released tuple keeps working, and a ``list[GroupRecord]`` is accepted by
    ``MulticastClient.send_mldv2_report``, whose parameter is a ``Sequence`` of that tuple. (It
    is not a :data:`MulticastGroupRecord`: ``list`` is invariant.)
    """

    __slots__ = ()
