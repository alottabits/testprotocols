"""VLAN id/name registry for a managed switch (distinct from ApplianceVlans)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.switch import VlanDef


@runtime_checkable
class SwitchVlans(Protocol):
    """Abstract contract for the switch VLAN registry."""

    def list_vlans(self) -> list[VlanDef]:
        """Return every configured VLAN."""
        ...

    def create_vlan(self, vlan: VlanDef) -> None:
        """Create or rename the VLAN ``vlan.vlan_id``.

        A driver whose product treats VLANs as implicit (no first-class CRUD)
        raises unsupported-capability here.
        """
        ...

    def delete_vlan(self, vlan_id: int) -> None:
        """Delete VLAN *vlan_id*. Raises unsupported-capability where VLANs are implicit."""
        ...
