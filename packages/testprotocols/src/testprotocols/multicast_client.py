"""Multicast client template.

Defines the abstract contract for sending multicast group membership reports
from a test client device.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from testprotocols.models.multicast import McastGroup, McastSource, MulticastGroupRecordType


@runtime_checkable
class MulticastClient(Protocol):
    """Abstract contract for multicast client operations."""

    def send_mldv2_report(
        self,
        mcast_group_record: Sequence[
            tuple[list[McastSource], McastGroup, MulticastGroupRecordType]
        ],
        count: int,
    ) -> None:
        """Send *count* MLDv2 membership report packets for the given group records.

        Each record is a :class:`~testprotocols.models.GroupRecord` (a named tuple, so a
        driver that unpacks ``(sources, group, record_type)`` keeps working). The parameter
        is a ``Sequence`` of the released tuple (released: the invariant ``list`` of
        :data:`~testprotocols.models.MulticastGroupRecord`), so both the released
        ``MulticastGroupRecord`` and a ``list[GroupRecord]`` are accepted. A plain tuple is
        deprecated; the parameter narrows to ``Sequence[GroupRecord]`` in a later release.
        """
        ...
