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
        """Create a VLAN interface for *vlan_id*.

        *vlan_id* is the VLAN number as text (``"100"``); it stays ``str`` because the
        released implementers declare ``str``.

        Deprecated: *vlan_id* as ``str``; it narrows to ``int``. Removal not before the first
        release 6 months after the release that deprecates it.
        """
        ...

    def delete_vlan_interface(self, vlan_id: str) -> None:
        """Delete the VLAN interface for *vlan_id* (text, as for
        :meth:`add_vlan_interface`).

        Deprecated: *vlan_id* as ``str``; it narrows to ``int``. Removal not before the first
        release 6 months after the release that deprecates it.
        """
        ...
