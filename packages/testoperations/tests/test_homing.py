"""Tests for testoperations.homing — VLAN-repositioning homing over sdwan_appliance protocols."""

from __future__ import annotations

from unittest.mock import MagicMock

from testoperations.homing import home_client
from testprotocols.models.sdwan_appliance import (
    SiteToSiteVpnConfig,
    VlanConfig,
    VpnRole,
    VpnSubnet,
)


def _vlan() -> VlanConfig:
    return VlanConfig(
        vlan_id=2639,
        name="qoe-rotterdam",
        subnet="10.1.30.0/24",
        appliance_ip="10.1.30.1",
    )


def _vpn_mock(subnets=None):
    vpn = MagicMock()
    vpn.get_vpn_config.return_value = SiteToSiteVpnConfig(
        role=VpnRole.SPOKE, hubs=[], subnets=list(subnets or [])
    )
    return vpn


def test_home_client_defines_and_advertises_on_target():
    vlan = _vlan()
    target_lan = MagicMock()
    target_vpn = _vpn_mock()

    home_client(vlan, target_lan, target_vpn)

    target_lan.set_vlan.assert_called_once_with(vlan)
    new_cfg = target_vpn.set_vpn_config.call_args.args[0]
    assert any(s.subnet == "10.1.30.0/24" and s.advertise for s in new_cfg.subnets)


def test_home_client_withdraws_from_previous_before_defining():
    vlan = _vlan()
    order: list[str] = []
    target_lan = MagicMock()
    target_lan.set_vlan.side_effect = lambda c: order.append("define")
    target_vpn = _vpn_mock()
    target_vpn.set_vpn_config.side_effect = lambda c: order.append("vpn-advertise")
    previous_lan = MagicMock()
    previous_lan.get_vlan.return_value = vlan  # present on previous
    previous_lan.delete_vlan.side_effect = lambda vid: order.append("withdraw")
    previous_vpn = _vpn_mock([VpnSubnet(subnet="10.1.30.0/24", advertise=True)])
    previous_vpn.set_vpn_config.side_effect = lambda c: order.append("vpn-withdraw")

    home_client(vlan, target_lan, target_vpn,
                previous_lan=previous_lan, previous_vpn=previous_vpn)

    previous_lan.delete_vlan.assert_called_once_with(2639)
    # previous advertisement withdrawn (subnet removed from previous vpn config)
    prev_cfg = previous_vpn.set_vpn_config.call_args.args[0]
    assert all(s.subnet != "10.1.30.0/24" for s in prev_cfg.subnets)
    # withdraw happens before define
    assert order == ["withdraw", "vpn-withdraw", "define", "vpn-advertise"]


def test_home_client_skips_withdraw_when_vlan_absent_on_previous():
    vlan = _vlan()
    target_lan = MagicMock()
    target_vpn = _vpn_mock()
    previous_lan = MagicMock()
    previous_lan.get_vlan.side_effect = KeyError(2639)  # not present
    previous_vpn = _vpn_mock()

    home_client(vlan, target_lan, target_vpn,
                previous_lan=previous_lan, previous_vpn=previous_vpn)

    previous_lan.delete_vlan.assert_not_called()
