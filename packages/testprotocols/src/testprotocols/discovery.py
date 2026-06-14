"""Read-only link-layer neighbour discovery (LLDP-normalized)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.switch import LldpNeighbor


@runtime_checkable
class Discovery(Protocol):
    """Abstract contract for neighbour discovery (read-only).

    A product that also runs a proprietary discovery protocol maps its neighbour
    data onto this LLDP-shaped read.
    """

    def get_neighbors(self, port: str | None = None) -> list[LldpNeighbor]:
        """Return discovered neighbours, optionally filtered to one *port*."""
        ...
