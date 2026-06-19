"""LAN VLAN + DHCP template — managed SD-WAN appliance.

Defines the abstract contract for a managed appliance's LAN side: per-VLAN
subnet/addressing and DHCP configuration, plus observed DHCP leases. This is the
appliance counterpart to a Linux host's interface + DHCP-server surfaces — an
appliance configures DHCP per VLAN, not via a host daemon.

In scope: list/get/set/delete VLAN configuration (incl. per-VLAN DHCP), and read
DHCP leases.

Out of scope: WAN uplink status (see ``appliance_uplinks``), L3 firewall
(see ``l3_firewall``), and host-style per-interface config (see ``ip_interface``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.sdwan_appliance import DhcpLease, VlanConfig


@runtime_checkable
class ApplianceVlans(Protocol):
    """Abstract contract for an appliance's LAN VLANs and DHCP."""

    def list_vlans(self) -> list[VlanConfig]:
        """Return every configured LAN VLAN."""
        ...

    def get_vlan(self, vlan_id: int) -> VlanConfig:
        """Return the VLAN with *vlan_id*.

        Raises KeyError if no VLAN with that id exists.
        """
        ...

    def set_vlan(self, config: VlanConfig) -> None:
        """Create or replace the VLAN identified by ``config.vlan_id``."""
        ...

    def delete_vlan(self, vlan_id: int) -> None:
        """Remove the LAN VLAN identified by *vlan_id*.

        Per-object remove, completing the VLAN CRUD surface (mirrors
        ``StaticRoutes.remove_static_route``). On management planes that model the
        LAN as one config blob, a driver implements this as read-modify-write of
        that module. Deleting a missing VLAN may raise or succeed by plane;
        callers needing idempotence should check first (``get_vlan`` raises
        KeyError when absent). A plane that cannot remove a required / last LAN
        VLAN raises unsupported-capability.
        """
        ...

    def get_dhcp_leases(self, vlan_id: int | None = None) -> list[DhcpLease]:
        """Return current DHCP leases, optionally filtered to one *vlan_id*.

        Best-effort read: several management planes publish no true lease
        table, so a driver may approximate from observed-client visibility
        (no expiry / binding state) or raise unsupported-capability. Tests
        should treat the result as observational evidence, not an exact
        lease-table assertion.
        """
        ...
