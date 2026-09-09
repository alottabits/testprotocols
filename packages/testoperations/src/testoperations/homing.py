"""Overlay-participation operations over the sdwan_appliance surface.

Two families share this module because both edit the same whole-replace
site-to-site VPN configuration (``SiteToSiteVpn.set_vpn_config`` takes the
complete overlay participation):

- **Client homing** (``home_client`` / ``realize`` / ``verify_home``): homing a
  client to a location = define the client's fixed LAN VLAN on that location's
  appliance and advertise its subnet into the overlay, withdrawing both from
  the client's previous appliance first (single-definer invariant). The client
  itself never moves; its VLAN/subnet are a fixed identity.
- **Single-subnet advertisement** (``set_subnet_advertised``): flip one local
  subnet's participation in the overlay — whatever makes the subnet local, a
  VLAN or a static route — leaving every other subnet, the role and the hubs
  untouched.

Vendor-agnostic and assertion-free: every argument is a resolved capability
protocol instance (``ApplianceVlans`` / ``SiteToSiteVpn``); callers interpret
results. No vendor SDK is imported here.
"""

from __future__ import annotations

from dataclasses import dataclass

from testprotocols.appliance_vlans import ApplianceVlans
from testprotocols.devices.sdwan import SdwanApplianceDevice
from testprotocols.models.sdwan_appliance import (
    SiteToSiteVpnConfig,
    VlanConfig,
    VpnPeerState,
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

    Withdrawing **drops** the subnet's entry: the homing callers remove the
    subnet's VLAN definition in the same operation, so the subnet is no longer
    local and an entry for it has nothing to describe. For a subnet that stays
    local after the withdrawal, use the public :func:`set_subnet_advertised`,
    which keeps the entry with the flag off. Subnets match by exact string
    equality.
    """
    cfg = vpn.get_vpn_config()
    subnets = [s for s in cfg.subnets if s.subnet != subnet]
    if advertise:
        subnets.append(VpnSubnet(subnet=subnet, advertise=True))
    vpn.set_vpn_config(SiteToSiteVpnConfig(role=cfg.role, hubs=cfg.hubs, subnets=subnets))


def set_subnet_advertised(vpn: SiteToSiteVpn, subnet: str, advertise: bool) -> None:
    """Read-modify-write *vpn* so *subnet* carries *advertise*; all else preserved.

    The overlay configuration is replaced whole (the ``SiteToSiteVpn``
    contract), so this reads it, changes exactly one thing and writes it back:

    - an entry for *subnet* that already exists keeps its position and takes
      the requested flag;
    - an absent entry is appended with ``advertise=True`` when advertising,
      and left absent when withdrawing;
    - the role and the hubs pass through unchanged.

    Subnets match by exact string equality — the same rule
    :func:`_set_advertise` and :func:`verify_home` apply; no CIDR
    normalisation.

    A converged state performs no write: when the rebuilt configuration equals
    the one read, ``set_vpn_config`` is not called — a configuration push that
    changes nothing is still a push. Idempotent. Assertion-free; raises only on
    operational failure.

    Sibling of the private :func:`_set_advertise`, which drops the entry on
    withdraw because its callers delete the subnet's VLAN in the same
    operation; this one keeps the entry with the flag off, for a subnet that
    stays local — a static route's, or a VLAN's that is not being removed.
    """
    cfg = vpn.get_vpn_config()
    subnets = [
        VpnSubnet(subnet=s.subnet, advertise=advertise) if s.subnet == subnet else s
        for s in cfg.subnets
    ]
    if advertise and not any(s.subnet == subnet for s in cfg.subnets):
        subnets.append(VpnSubnet(subnet=subnet, advertise=True))
    rebuilt = SiteToSiteVpnConfig(role=cfg.role, hubs=cfg.hubs, subnets=subnets)
    if rebuilt == cfg:
        return
    vpn.set_vpn_config(rebuilt)


def verify_home(
    vlan: VlanConfig,
    target_lan: ApplianceVlans,
    target_vpn: SiteToSiteVpn,
) -> dict[str, object]:
    """MX-side verification that *vlan* is homed on the target appliance.

    Reads (no writes): the VLAN is defined with the expected subnet/gateway, its
    subnet is advertised into the overlay, and every VPN peer is REACHABLE.
    ``peers_reachable`` is observational — empty peer list (no overlay) reads as
    False. The in-guest half (gateway reachability from the test namespace) is
    the plugin's ``verify_homing``; the caller composes the two vantage points.
    """
    try:
        defined = target_lan.get_vlan(vlan.vlan_id)
        vlan_defined = defined.subnet == vlan.subnet and defined.appliance_ip == vlan.appliance_ip
    except KeyError:
        defined = None
        vlan_defined = False

    cfg = target_vpn.get_vpn_config()
    subnet_advertised = any(s.subnet == vlan.subnet and s.advertise for s in cfg.subnets)

    peers = target_vpn.get_vpn_peers()
    peers_reachable = bool(peers) and all(p.state is VpnPeerState.REACHABLE for p in peers)

    return {
        "vlan_defined": vlan_defined,
        "subnet_advertised": subnet_advertised,
        "peers_reachable": peers_reachable,
        "details": {
            "defined_subnet": getattr(defined, "subnet", None),
            "defined_gateway": getattr(defined, "appliance_ip", None),
            "peer_states": {p.name: p.state.value for p in peers},
        },
    }


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


@dataclass
class HomeAssignment:
    """A desired home: the client's fixed VLAN on a specific target appliance."""

    vlan: VlanConfig
    target: SdwanApplianceDevice


def realize(
    assignments: list[HomeAssignment],
    all_appliances: list[SdwanApplianceDevice],
) -> None:
    """Apply a whole homing topology idempotently, enforcing single-definer.

    For each assignment: withdraw the VLAN (definition + advertisement) from every
    appliance that is NOT its target, then define + advertise on the target. Safe
    to re-run; restore-to-default is this function with the default assignments.
    """
    for a in assignments:
        for ap in all_appliances:
            if ap is a.target:
                continue
            _delete_if_present(ap.lan, a.vlan.vlan_id)
            _set_advertise(ap.vpn, a.vlan.subnet, advertise=False)
        a.target.lan.set_vlan(a.vlan)
        _set_advertise(a.target.vpn, a.vlan.subnet, advertise=True)
