"""Router / WAN edge template.

Defines the abstract contract for **reading** a WAN edge router's state:
interface status, path metrics, link health, telemetry, and the routing
table. The surface is read-only so it holds for every WAN-edge archetype —
including API-managed appliances, whose management planes expose reads but
no link administration. Forced link-down lives on ``wan_link_admin``
(host-substrate only; see SPLITS.md).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from testprotocols._compat import deprecated
from testprotocols.models.wan_edge import (
    LinkHealthReport,
    LinkStatus,
    PathMetrics,
    RouteEntry,
    Telemetry,
)


@runtime_checkable
class Router(Protocol):
    """Abstract contract for reading WAN edge router state."""

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

    def read_telemetry(self) -> Telemetry:
        """Return the device's current resource telemetry: uptime, CPU load and
        memory use (:class:`~testprotocols.models.Telemetry`)."""
        ...

    @deprecated(
        "Deprecated: use read_telemetry. Removal not before the first release 6 "
        "months after the release that deprecates it.",
        category=None,
    )
    def get_telemetry(self) -> dict[str, Any]:  # type: ignore[explicit-any]  # released signature kept until removal
        """Return a dict of current device telemetry data: the keys ``uptime_seconds``,
        ``cpu_load_percent`` and ``mem_used_percent`` (a key is absent when the device
        does not report it), the reported fields of ``read_telemetry()``.

        Deprecated: use :meth:`read_telemetry`. Removal not before the first release 6 months after
        the release that deprecates it.
        """
        ...

    def get_routing_table(self) -> list[RouteEntry]:
        """Return the current routing table as a list of RouteEntry records."""
        ...
