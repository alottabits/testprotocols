"""Read-only routing-table (RIB) read for a switch — RouteEntry, shared with Router."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.wan_edge import RouteEntry


@runtime_checkable
class RoutingRead(Protocol):
    """Abstract contract for the switch routing-table read.

    The config-view read (connected/static/configured routes) is universal; the
    dynamic-learned RIB facet is best-effort — a product that is config-only on
    routing state raises unsupported-capability for the learned routes.
    """

    def get_routing_table(self) -> list[RouteEntry]:
        """Return the routing table as RouteEntry records (origin-classified
        where the product exposes it)."""
        ...
