"""First-hop security — DHCP snooping + Dynamic ARP Inspection.

Rogue-DHCP control is the DHCP-snooping *intent*: divergent vendor shapes
(server allow/block, port-trust snooping, IMPB) normalize onto one surface.
Per-port trust / rate-limit / binding-table read are optional sub-methods; a
driver lacking one raises unsupported-capability rather than failing the
baseline. IP Source Guard is a deferred optional extension (see GAPS.md).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.switch import BindingSource, FhsBinding, FhsScope, FhsTrustState


@runtime_checkable
class FirstHopSecurity(Protocol):
    """Abstract contract for DHCP snooping + Dynamic ARP Inspection."""

    def set_dhcp_snooping(
        self, scope: FhsScope, enabled: bool, vlan: int | None = None
    ) -> None:
        """Enable/disable DHCP snooping globally or per-VLAN. A switch-wide-only
        product maps ``PER_VLAN`` to ``GLOBAL`` or raises unsupported-capability."""
        ...

    def set_dhcp_snooping_trust(self, port: str, trust: FhsTrustState) -> None:
        """Set the per-port snooping trust state. Optional — unsupported-capability
        where the product has no per-port trust (e.g. MAC allow/block only)."""
        ...

    def get_dhcp_bindings(self) -> list[FhsBinding]:
        """Return the snooping binding table. Optional — unsupported-capability
        where no binding table is published."""
        ...

    def set_dai(
        self,
        scope: FhsScope,
        enabled: bool,
        vlan: int | None = None,
        binding_source: BindingSource = BindingSource.DYNAMIC_SNOOPING,
    ) -> None:
        """Enable/disable Dynamic ARP Inspection. Products without DAI raise
        unsupported-capability."""
        ...

    def set_arp_trust(self, port: str, trust: FhsTrustState) -> None:
        """Set the per-port ARP-inspection trust state."""
        ...
