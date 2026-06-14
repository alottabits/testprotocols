"""Read-only forwarding-database (FDB / MAC address-table) read."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.l2_common import MacTableEntry


@runtime_checkable
class MacTable(Protocol):
    """Abstract contract for the FDB read.

    A product with no FDB API raises unsupported-capability. A raw-dump white-box
    extension is a LEVELS.md candidate (``MacTableWhiteBox``).
    """

    def get_mac_table(self, vlan: int | None = None) -> list[MacTableEntry]:
        """Return FDB entries, optionally filtered to one *vlan*."""
        ...
