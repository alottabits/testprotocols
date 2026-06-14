"""Per-SVI DHCP server/relay configuration (reuses appliance DHCP models)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.sdwan_appliance import DhcpLease
from testprotocols.models.switch_routing import InterfaceDhcpConfig


@runtime_checkable
class InterfaceDhcp(Protocol):
    """Abstract contract for per-interface DHCP server/relay.

    Best-effort lease read: a product without a true lease table may approximate
    or raise unsupported-capability on ``get_dhcp_leases``.
    """

    def set_interface_dhcp(self, config: InterfaceDhcpConfig) -> None:
        """Create or replace the DHCP config for ``config.interface``."""
        ...

    def get_interface_dhcp(self, interface: str) -> InterfaceDhcpConfig:
        """Return the DHCP config for *interface*."""
        ...

    def get_dhcp_leases(self, interface: str | None = None) -> list[DhcpLease]:
        """Return current DHCP leases (best-effort; a product without a true
        lease table may approximate or raise unsupported-capability)."""
        ...
