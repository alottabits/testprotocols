"""ARP / Client template.

Defines the abstract contract for ARP client operations including cache
management and table inspection.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols._compat import deprecated
from testprotocols.models.networking import ArpEntry


@runtime_checkable
class ArpClient(Protocol):
    """Abstract contract for ARP client operations."""

    def flush_arp_cache(self) -> None:
        """Flush all entries from the ARP cache."""
        ...

    @deprecated(
        "Deprecated: use read_arp_table. Removal not before the first release 6 "
        "months after the release that deprecates it.",
        category=None,
    )
    def get_arp_table(self) -> str:
        """Return the current ARP table as the device prints it.

        The text cannot be rebuilt from the entries :meth:`read_arp_table` returns.

        Deprecated: use :meth:`read_arp_table`. Removal not before the first release 6 months after
        the release that deprecates it.
        """
        ...

    def read_arp_table(self) -> list[ArpEntry]:
        """Return the complete entries of the current ARP table; an incomplete entry (no
        hardware address yet) is left out."""
        ...

    def delete_arp_table_entry(self, ip: str, intf: str) -> None:
        """Delete the ARP table entry for *ip* on interface *intf*."""
        ...
