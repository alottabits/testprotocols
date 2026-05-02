"""Firewall / PortForwarding template.

Defines the abstract contract for named external-port → internal-host:port
mappings, plus the single DMZ-host shortcut. Mappings are identified by a
stable logical *name*.

This is intentionally higher-level than ``nat``: drivers may lower a
``PortMapping`` to a DNAT primitive, a TR-069 ``Device.NAT.PortMapping``
object, a UPnP-IGD / PCP entry, or a vendor port-forward CLI — tests
never need to know which.

In scope: lifecycle of named port mappings and the single-DMZ-host
configuration.

Out of scope: SNAT / raw DNAT primitives (see ``nat``), packet-filter
rules (see ``packet_filter``), and client-side UPnP-IGD rule injection
(see ``upnp_client``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.firewall import PortMapping


@runtime_checkable
class PortForwarding(Protocol):
    """Abstract contract for named port mappings and the DMZ host."""

    # --- Port-mapping lifecycle ---

    def add_port_mapping(self, mapping: PortMapping) -> None:
        """Install a port mapping.

        Raises ValueError on a duplicate ``mapping.name``, on
        *external_port* / *internal_port* outside ``1..65535``, or on
        *protocol* not in ``{"tcp", "udp", "tcp-udp"}``.
        """
        ...

    def remove_port_mapping(self, name: str) -> None:
        """Remove the port mapping identified by *name*.

        Raises KeyError if no mapping with that name exists.
        """
        ...

    def list_port_mappings(self) -> list[PortMapping]:
        """Return all installed port mappings."""
        ...

    def get_port_mapping(self, name: str) -> PortMapping:
        """Return the port mapping identified by *name*.

        Raises KeyError if no mapping with that name exists.
        """
        ...

    def set_port_mapping_enabled(self, name: str, enabled: bool) -> None:
        """Enable or disable an existing port mapping without removing it.

        Raises KeyError if no mapping with that name exists.
        """
        ...

    # --- DMZ host ---

    def set_dmz_host(self, host: str | None) -> None:
        """Set the DMZ-host destination, or pass ``None`` to clear DMZ.

        When set, all unsolicited inbound traffic that does not match
        any other port mapping is forwarded to *host*.

        Raises ValueError if *host* is not a parseable IP address.
        """
        ...

    def get_dmz_host(self) -> str | None:
        """Return the current DMZ host, or ``None`` if no DMZ host is set."""
        ...
