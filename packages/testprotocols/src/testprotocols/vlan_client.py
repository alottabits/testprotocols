"""VLAN / Client template.

Defines the abstract contract for VLAN client operations including
virtual interface creation and deletion.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class VlanClient(Protocol):
    """Abstract contract for VLAN client operations."""

    def add_vlan_interface(self, vlan_id: str) -> None:
        """Create a VLAN interface for *vlan_id*."""
        ...

    def delete_vlan_interface(self, vlan_id: str) -> None:
        """Delete the VLAN interface for *vlan_id*."""
        ...
