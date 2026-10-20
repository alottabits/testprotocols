"""Automatic port mapping — the protocols by which LAN hosts request their own mappings.

A gateway lets its LAN hosts open inbound ports through UPnP IGD, PCP or
NAT-PMP, each enabled on its own, and keeps one table of the mappings they
requested. The administrator's own mappings stay on ``firewall``; origin and
lease distinguish the two tables.

In scope: enable or disable each protocol, read the enable state, list the
requested mappings.

Out of scope: the administrator's port mappings (see
``firewall.list_port_mappings``), the host-side client (see ``upnp_client``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.cpe_gateway import AutoMappingProtocol, AutoPortMappingEntry


@runtime_checkable
class AutoPortMapping(Protocol):
    """Abstract contract for the gateway's automatic port mapping."""

    def set_enabled(self, protocol: AutoMappingProtocol, enabled: bool) -> None:
        """Enable or disable *protocol*; paired read ``get_enabled``.

        Raises ``NotSupportedError`` for a protocol the family publishes no toggle for (a
        per-value case). A family whose one toggle enables or disables automatic mapping as a
        whole maps ``UPNP_IGD`` onto it and raises for the other values.
        """
        ...

    def get_enabled(self, protocol: AutoMappingProtocol) -> bool:
        """Return whether *protocol* is enabled; raises ``NotSupportedError`` for a protocol
        the family publishes no toggle for."""
        ...

    def list_mappings(self) -> list[AutoPortMappingEntry]:
        """Return the mappings LAN hosts requested, distinct from the administrator's
        (``firewall.list_port_mappings``) by ``origin`` and ``remaining_lease_s``; a family
        that publishes one protocol's table only raises ``NotSupportedError`` for none and
        reports that table."""
        ...
