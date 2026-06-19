"""Tests for testoperations.homing — VLAN-repositioning homing over sdwan_appliance protocols."""

from __future__ import annotations

from unittest.mock import MagicMock

from testoperations.homing import home_client, verify_home
from testprotocols.models.sdwan_appliance import (
    SiteToSiteVpnConfig,
    VlanConfig,
    VpnPeerState,
    VpnPeerStatus,
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


def test_verify_home_all_true_when_defined_advertised_and_peers_reachable():
    vlan = _vlan()
    target_lan = MagicMock()
    target_lan.get_vlan.return_value = vlan
    target_vpn = _vpn_mock([VpnSubnet(subnet="10.1.30.0/24", advertise=True)])
    target_vpn.get_vpn_peers.return_value = [
        VpnPeerStatus(name="ermelo", state=VpnPeerState.REACHABLE),
        VpnPeerStatus(name="amsterdam", state=VpnPeerState.REACHABLE),
    ]

    v = verify_home(vlan, target_lan, target_vpn)

    assert v["vlan_defined"] is True
    assert v["subnet_advertised"] is True
    assert v["peers_reachable"] is True


def test_verify_home_false_when_vlan_absent():
    vlan = _vlan()
    target_lan = MagicMock()
    target_lan.get_vlan.side_effect = KeyError(2639)
    target_vpn = _vpn_mock()
    target_vpn.get_vpn_peers.return_value = []

    v = verify_home(vlan, target_lan, target_vpn)

    assert v["vlan_defined"] is False
    assert v["subnet_advertised"] is False
    assert v["peers_reachable"] is False


def test_verify_home_peers_reachable_false_when_any_unreachable():
    vlan = _vlan()
    target_lan = MagicMock()
    target_lan.get_vlan.return_value = vlan
    target_vpn = _vpn_mock([VpnSubnet(subnet="10.1.30.0/24", advertise=True)])
    target_vpn.get_vpn_peers.return_value = [
        VpnPeerStatus(name="ermelo", state=VpnPeerState.REACHABLE),
        VpnPeerStatus(name="amsterdam", state=VpnPeerState.UNREACHABLE),
    ]

    v = verify_home(vlan, target_lan, target_vpn)
    assert v["peers_reachable"] is False


from testoperations.homing import HomeAssignment, realize


def _appliance(name: str, defined_vlan_ids=()):
    """Fake SdwanApplianceDevice exposing .lan and .vpn."""
    ap = MagicMock()
    ap.name = name
    present = set(defined_vlan_ids)

    def get_vlan(vid):
        if vid in present:
            return _vlan()
        raise KeyError(vid)

    ap.lan.get_vlan.side_effect = get_vlan
    ap.lan.delete_vlan.side_effect = lambda vid: present.discard(vid)
    ap.lan.set_vlan.side_effect = lambda c: present.add(c.vlan_id)
    ap.vpn.get_vpn_config.return_value = SiteToSiteVpnConfig(
        role=VpnRole.SPOKE, hubs=[], subnets=[]
    )
    return ap


def test_realize_defines_on_target_and_withdraws_elsewhere():
    rotterdam = _appliance("rotterdam")
    amsterdam = _appliance("amsterdam", defined_vlan_ids=[2639])  # stray definition
    vlan = _vlan()

    realize([HomeAssignment(vlan=vlan, target=rotterdam)], [rotterdam, amsterdam])

    rotterdam.lan.set_vlan.assert_called_once_with(vlan)
    amsterdam.lan.delete_vlan.assert_called_once_with(2639)  # single-definer enforced


def test_realize_is_idempotent_on_clean_apply():
    rotterdam = _appliance("rotterdam")
    amsterdam = _appliance("amsterdam")
    vlan = _vlan()
    assignments = [HomeAssignment(vlan=vlan, target=rotterdam)]

    realize(assignments, [rotterdam, amsterdam])
    realize(assignments, [rotterdam, amsterdam])  # second apply == same end state

    # target defined both times; non-target never had it, so never deleted
    assert rotterdam.lan.set_vlan.call_count == 2
    amsterdam.lan.delete_vlan.assert_not_called()


def test_realize_restores_default_after_a_rehome():
    rotterdam = _appliance("rotterdam")
    amsterdam = _appliance("amsterdam", defined_vlan_ids=[2639])  # moved here by a scenario
    vlan = _vlan()

    # restore default: qoe VLAN belongs on rotterdam
    realize([HomeAssignment(vlan=vlan, target=rotterdam)], [rotterdam, amsterdam])

    amsterdam.lan.delete_vlan.assert_called_once_with(2639)
    rotterdam.lan.set_vlan.assert_called_once_with(vlan)
