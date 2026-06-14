"""Read-only per-port link state, speed/duplex, and counters."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.switch import PortStatusEntry


@runtime_checkable
class PortStatus(Protocol):
    """Abstract contract for per-port status read.

    Replaces the host-shaped ``ip_interface`` read for this archetype.
    """

    def list_port_status(self) -> list[PortStatusEntry]:
        """Return status for every port."""
        ...

    def get_port_status(self, name: str) -> PortStatusEntry:
        """Return status for port *name*. Raises KeyError if absent."""
        ...
