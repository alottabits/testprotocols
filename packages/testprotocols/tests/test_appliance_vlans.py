"""Protocol-conformance tests for ApplianceVlans (runtime_checkable structural check)."""

from __future__ import annotations

from testprotocols.appliance_vlans import ApplianceVlans


class _Complete:
    """Has every ApplianceVlans member, including delete_vlan."""

    def list_vlans(self): ...
    def get_vlan(self, vlan_id): ...
    def set_vlan(self, config): ...
    def delete_vlan(self, vlan_id): ...
    def get_dhcp_leases(self, vlan_id=None): ...


class _NoDelete:
    """Missing delete_vlan — must NOT satisfy the protocol once delete_vlan is declared."""

    def list_vlans(self): ...
    def get_vlan(self, vlan_id): ...
    def set_vlan(self, config): ...
    def get_dhcp_leases(self, vlan_id=None): ...


def test_complete_impl_satisfies_protocol():
    assert isinstance(_Complete(), ApplianceVlans)


def test_delete_vlan_is_required_by_protocol():
    # runtime_checkable isinstance requires every declared member be present.
    assert not isinstance(_NoDelete(), ApplianceVlans)
