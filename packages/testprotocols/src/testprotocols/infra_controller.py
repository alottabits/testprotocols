"""Infra-controller capability template.

Abstract contract for environment/fabric control delegated by the test
orchestrator to a hypervisor (vSphere). It reads and (for re-homing) moves a
VM NIC's port-group, and asserts a named port-group is present. It does NOT
create fabric — the lab carries the test VLANs already.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class InfraController(Protocol):
    """Read / presence-check / move a VM NIC's port-group."""

    def get_nic_portgroup(self, vm_name: str, nic_index: int) -> str:
        """Return the portgroup name backing NIC *nic_index* on *vm_name*."""
        ...

    def ensure_port_group(self, name: str) -> None:
        """Assert a portgroup named *name* exists (raise if absent). No create."""
        ...

    def set_nic_portgroup(self, vm_name: str, nic_index: int, portgroup: str) -> None:
        """Repoint NIC *nic_index* on *vm_name* onto the named *portgroup*."""
        ...
