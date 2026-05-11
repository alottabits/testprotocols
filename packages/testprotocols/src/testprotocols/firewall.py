"""Firewall template — gateway-tier rule administration + port forwarding.

Extends ``PacketFilter`` with port-forwarding methods (named external→internal
port mappings, DMZ host). Models the OpenWrt-UCI ``firewall`` config and
TR-181 ``Device.Firewall.*`` subtree as one coherent gateway subsystem:
admins reason about packet rules and port forwards together, and an
``iptables-save`` dump captures both in one stream.

In scope: the full ``PacketFilter`` rule-lifecycle surface (inherited)
plus port-mapping lifecycle and the single DMZ-host shortcut.

Out of scope: low-level NAT primitives (see ``nat``), zone-based policy
(see ``firewall_zones``), conntrack inspection (see ``conntrack``), and
client-side UPnP-IGD rule injection (see ``upnp_client``).

Devices that have rule administration but no port forwarding (clients,
infra services) satisfy only the narrower ``PacketFilter`` Protocol; they
should not be typed against ``Firewall``.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.firewall import PortMapping
from testprotocols.packet_filter import PacketFilter


@runtime_checkable
class Firewall(PacketFilter, Protocol):
    """Gateway-tier firewall: rule administration + port forwarding.

    Liskov extension of ``PacketFilter``. Any driver satisfying ``Firewall``
    automatically satisfies ``PacketFilter`` via Protocol inheritance.
    """

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


@runtime_checkable
class FirewallWhiteBox(Firewall, Protocol):
    """White-box extension of Firewall for raw kernel-level introspection.

    Linux drivers that can shell into the box satisfy this extension by
    capturing the underlying iptables / nftables ruleset (which natively
    covers both filter rules and DNAT / port-forward entries in one
    serialisation). Vendor-RTOS or locked-down devices typically satisfy
    only the base ``Firewall`` Protocol; tests requiring kernel-level
    verification should pin against ``FirewallWhiteBox`` and accept the
    collection-skip on drivers that don't satisfy it (per the
    ``@white_box`` scenario tag rule).
    """

    def get_kernel_iptables_dump(self) -> str:
        """Return the raw ``iptables-save`` output (legacy iptables backend).

        For drivers running on a Linux kernel with the legacy iptables
        backend. Format is the standard iptables-save serialisation,
        spanning filter chains, NAT chains, and DNAT / port-forward
        entries in one stream.
        """
        ...

    def get_nftables_ruleset(self) -> str:
        """Return the raw ``nft list ruleset`` output (nftables backend).

        For drivers running on a Linux kernel with the nftables backend.
        Format is the standard nftables ruleset serialisation, spanning
        the full ruleset across all tables and families.
        """
        ...
