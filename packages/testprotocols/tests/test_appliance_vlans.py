"""Protocol-conformance tests for ApplianceVlans (runtime_checkable structural check)."""

from __future__ import annotations

from testprotocols.appliance_vlans import ApplianceVlans
from testprotocols.models.sdwan_appliance import DhcpLease, VlanConfig


class _Complete:
    """Has every ApplianceVlans member, including delete_vlan.

    Signatures mirror the protocol for documentation only — ``runtime_checkable``
    ``isinstance`` checks member presence, not shape, so these bodies are never
    reached.
    """

    def list_vlans(self) -> list[VlanConfig]:
        raise NotImplementedError

    def get_vlan(self, vlan_id: int) -> VlanConfig:
        raise NotImplementedError

    def set_vlan(self, config: VlanConfig) -> None: ...

    def delete_vlan(self, vlan_id: int) -> None: ...

    def get_dhcp_leases(self, vlan_id: int | None = None) -> list[DhcpLease]:
        raise NotImplementedError


class _NoDelete:
    """Missing delete_vlan — must NOT satisfy the protocol once delete_vlan is declared."""

    def list_vlans(self) -> list[VlanConfig]:
        raise NotImplementedError

    def get_vlan(self, vlan_id: int) -> VlanConfig:
        raise NotImplementedError

    def set_vlan(self, config: VlanConfig) -> None: ...

    def get_dhcp_leases(self, vlan_id: int | None = None) -> list[DhcpLease]:
        raise NotImplementedError


def test_complete_impl_satisfies_protocol() -> None:
    assert isinstance(_Complete(), ApplianceVlans)


def test_delete_vlan_is_required_by_protocol() -> None:
    # runtime_checkable isinstance requires every declared member be present.
    assert not isinstance(_NoDelete(), ApplianceVlans)
