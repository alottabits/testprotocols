"""Host table — the LAN hosts the gateway knows, as one joined read.

A gateway knows its hosts from its leases, its neighbour tables and its
station lists. A family that publishes one host table reports it; a family
that publishes no single table joins those sources inside ``list_hosts``, a
mapping of three reads with no device state changed and no wait, stating in
its ``lossy:`` line which fields each source lacks.

In scope: the host list and one host by MAC.

Out of scope: the leases themselves (see ``interface_dhcp``), the stations on
one network (see ``wifi_stations``), blocking a host (see ``host_filter``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.cpe_gateway import LanHost


@runtime_checkable
class HostTable(Protocol):
    """Abstract contract for the gateway's host table."""

    def list_hosts(self) -> list[LanHost]:
        """Return every host the gateway knows.

        ``LanHost.mac`` is the canonical lowercase colon-separated form, canonicalised by the
        driver. ``attachment`` is ``None`` where the family does not publish how the host
        attaches or the medium is outside the closed ``HostAttachment`` set.
        """
        ...

    def get_host(self, mac: str) -> LanHost:
        """Return the host *mac*; any case is accepted and normalised to the canonical
        lowercase colon-separated form before the lookup."""
        ...
