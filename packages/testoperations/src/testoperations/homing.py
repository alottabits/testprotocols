"""QoE-client homing operations — VLAN repositioning over the sdwan_appliance surface.

Homing a client to a location = define the client's fixed LAN VLAN on that
location's appliance and advertise its subnet into the site-to-site VPN overlay,
withdrawing both from the client's previous appliance first (single-definer
invariant). The client itself never moves; its VLAN/subnet are a fixed identity.

Vendor-agnostic and assertion-free: every argument is a resolved capability
protocol instance (``ApplianceVlans`` / ``SiteToSiteVpn``); callers interpret
results. No vendor SDK is imported here.
"""

from __future__ import annotations

from testprotocols.appliance_vlans import ApplianceVlans
from testprotocols.models.sdwan_appliance import (
    SiteToSiteVpnConfig,
    VlanConfig,
    VpnSubnet,
)
from testprotocols.site_to_site_vpn import SiteToSiteVpn


def _delete_if_present(lan: ApplianceVlans, vlan_id: int) -> None:
    """Delete *vlan_id* from *lan* only if it currently exists (idempotent)."""
    try:
        lan.get_vlan(vlan_id)
    except KeyError:
        return
    lan.delete_vlan(vlan_id)


def _set_advertise(vpn: SiteToSiteVpn, subnet: str, advertise: bool) -> None:
    """Read-modify-write *vpn* so *subnet* is advertised (or not), leaving role/hubs intact.

    The overlay config is replaced whole (protocol contract), so we filter the
    subnet out and re-add it with the desired flag — idempotent either way.
    """
    cfg = vpn.get_vpn_config()
    subnets = [s for s in cfg.subnets if s.subnet != subnet]
    if advertise:
        subnets.append(VpnSubnet(subnet=subnet, advertise=True))
    vpn.set_vpn_config(SiteToSiteVpnConfig(role=cfg.role, hubs=cfg.hubs, subnets=subnets))


def home_client(
    vlan: VlanConfig,
    target_lan: ApplianceVlans,
    target_vpn: SiteToSiteVpn,
    *,
    previous_lan: ApplianceVlans | None = None,
    previous_vpn: SiteToSiteVpn | None = None,
) -> None:
    """Home a client whose fixed LAN VLAN is *vlan* onto the target appliance.

    Withdraw-before-define: if a previous appliance is given, remove the VLAN
    definition and its advertisement there first, then define + advertise on the
    target. Idempotent — re-homing to the same target replaces the VLAN and
    re-advertises the subnet with no duplication.
    """
    if previous_lan is not None:
        _delete_if_present(previous_lan, vlan.vlan_id)
    if previous_vpn is not None:
        _set_advertise(previous_vpn, vlan.subnet, advertise=False)
    target_lan.set_vlan(vlan)
    _set_advertise(target_vpn, vlan.subnet, advertise=True)
