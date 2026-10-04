"""ARP / Client template.

Defines the abstract contract for ARP client operations including cache
management and table inspection.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.networking import ArpEntry


@runtime_checkable
class ArpClient(Protocol):
    """Abstract contract for ARP client operations."""

    def flush_arp_cache(self) -> None:
        """Flush all entries from the ARP cache."""
        ...

    def get_arp_table(self) -> str:
        """Deprecated: use :meth:`read_arp_table`, which returns typed entries.

        Returns the current ARP table as the device prints it. A driver keeps returning that
        text until the removal step (it warns with
        ``warn_renamed("get_arp_table", "read_arp_table")``); the text cannot be rebuilt
        from the entries.
        """
        ...

    def read_arp_table(self) -> list[ArpEntry]:
        """Return the complete entries of the current ARP table; an incomplete entry (no
        hardware address yet) is left out."""
        ...

    def delete_arp_table_entry(self, ip: str, intf: str) -> None:
        """Delete the ARP table entry for *ip* on interface *intf*."""
        ...
