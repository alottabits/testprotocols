"""Router / WAN edge template.

Defines the abstract contract for WAN edge router operations including
interface status, path metrics, link health, and routing table management.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from testprotocols.models.wan_edge import (
    LinkHealthReport,
    LinkStatus,
    PathMetrics,
    RouteEntry,
)


@runtime_checkable
class Router(Protocol):
    """Abstract contract for WAN edge router operations."""

    def get_active_wan_interface(self, flow_dst: str | None = None) -> str | None:
        """Return the name of the active WAN interface, or ``None`` if no uplink
        is currently active (for a given ``flow_dst``, if there is no active path
        to it). "No active uplink" is an expected operational state — e.g. while
        a failover test has every uplink impaired — not an error; use
        ``get_wan_interface_status`` for per-uplink detail."""
        ...

    def get_wan_interface_status(self) -> dict[str, LinkStatus]:
        """Return a mapping of WAN interface names to their current link status."""
        ...

    def get_wan_path_metrics(self) -> dict[str, PathMetrics]:
        """Return a mapping of WAN interface names to measured path metrics."""
        ...

    def get_link_health(self, wan_label: str) -> LinkHealthReport:
        """Return a comprehensive health report for the named WAN link."""
        ...

    def get_telemetry(self) -> dict[str, Any]:
        """Return a dict of current device telemetry data."""
        ...

    def bring_wan_down(self, label: str) -> None:
        """Bring down the WAN interface identified by *label*."""
        ...

    def bring_wan_up(self, label: str) -> None:
        """Bring up the WAN interface identified by *label*."""
        ...

    def get_routing_table(self) -> list[RouteEntry]:
        """Return the current routing table as a list of RouteEntry records."""
        ...
