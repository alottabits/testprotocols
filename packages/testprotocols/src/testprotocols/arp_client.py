"""ARP / Client template.

Defines the abstract contract for ARP client operations including cache
management and table inspection.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ArpClient(Protocol):
    """Abstract contract for ARP client operations."""

    def flush_arp_cache(self) -> None:
        """Flush all entries from the ARP cache."""
        ...

    def get_arp_table(self) -> str:
        """Return the current ARP table as a string."""
        ...

    def delete_arp_table_entry(self, ip: str, intf: str) -> None:
        """Delete the ARP table entry for *ip* on interface *intf*."""
        ...
