"""Multicast group record types and type aliases."""
from __future__ import annotations

from enum import Enum


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
"""A list of (sources, group, record_type) tuples representing IGMPv3 group records."""
