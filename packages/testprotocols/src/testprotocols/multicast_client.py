"""Multicast client template.

Defines the abstract contract for sending multicast group membership reports
from a test client device.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.multicast import MulticastGroupRecord


@runtime_checkable
class MulticastClient(Protocol):
    """Abstract contract for multicast client operations."""

    def send_mldv2_report(self, mcast_group_record: MulticastGroupRecord, count: int) -> None:
        """Send *count* MLDv2 membership report packets for the given group records."""
        ...
