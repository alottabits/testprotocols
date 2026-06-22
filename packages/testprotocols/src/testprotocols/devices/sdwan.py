"""SD-WAN device archetypes."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.appliance_nat import ApplianceNat
from testprotocols.appliance_uplinks import ApplianceUplinks
from testprotocols.appliance_vlans import ApplianceVlans
from testprotocols.bgp import Bgp
from testprotocols.conntrack import Conntrack
from testprotocols.content_filtering import ContentFiltering
from testprotocols.devices import register_device_type
from testprotocols.devices.base import BaseDeviceProtocol
from testprotocols.ip_interface import IpInterface
from testprotocols.l3_firewall import L3Firewall
from testprotocols.l7_firewall import L7Firewall
from testprotocols.nat import Nat
from testprotocols.pcap_capture import PcapCapture
from testprotocols.router import Router
from testprotocols.sdwan_policy_manager import SdwanPolicyManager
from testprotocols.site_to_site_vpn import SiteToSiteVpn
from testprotocols.static_routes import StaticRoutes
from testprotocols.syslog_config import SyslogConfig
from testprotocols.threat_prevention import ThreatPrevention
from testprotocols.traffic_shaping import TrafficShaping
from testprotocols.wan_link_admin import WanLinkAdmin


@runtime_checkable
class SdwanRouterDevice(BaseDeviceProtocol, Protocol):
    """SD-WAN router archetype — branch / edge router with policy-based path selection.

    Combines a generic routing read surface, WAN link administration (forced
    link up/down — a host-substrate lever this Linux twin *can* exercise),
    SD-WAN policy management (path / app steering), IP interface management,
    packet capture, NAT, and connection tracking — the full set of L3 levers
    a test needs to exercise SD-WAN behaviour end to end. Traffic impairment (netem) is on the
    TrafficControllerDevice archetype — a separate device sitting between the
    router and its WAN peers — not on the router itself; see
    SPLITS.md for the rationale.
    """

    routing: Router
    wan_admin: WanLinkAdmin
    static_routes: StaticRoutes
    bgp: Bgp
    sdwan_policy: SdwanPolicyManager
    ip_interface: IpInterface
    pcap: PcapCapture
    nat: Nat
    conntrack: Conntrack


register_device_type("linux_sdwan_router", SdwanRouterDevice)


@runtime_checkable
class SdwanApplianceDevice(BaseDeviceProtocol, Protocol):
    """Managed SD-WAN **appliance** archetype — vendor-neutral.

    The capability surface a cloud-/controller-managed SD-WAN appliance exposes
    through its management API — satisfiable by any vendor's driver. Distinct
    from ``SdwanRouterDevice`` (the Linux digital twin, ``linux_sdwan_router``):
    an appliance is driven by an API, not a shell, so the host substrate
    capabilities — ``conntrack``, ``pcap``, ``ip_interface``, and the iptables
    ``nat`` — are deliberately **not** here; they remain on the twin. Packet
    capture is the TrafficControllerDevice's job (see SPLITS.md), not the
    appliance's.

    Firewall is split by layer (``l3_firewall`` / ``l7_firewall``) and content
    filtering is its own surface; NAT here is the appliance's 1:1 / 1:Many /
    port-forwarding (``appliance_nat``), not the host iptables primitives.
    Site-to-site VPN overlay participation — role, hubs, advertised subnets,
    peer status — is the ``vpn`` surface; the overlay's firewall rules stay on
    ``l3_firewall``. Forced link-down (``wan_admin``) is likewise absent: an
    API-managed appliance cannot admin-down its own uplink, so ``routing`` here
    is the read-only surface and link administration stays on the twin.
    """

    routing: Router
    static_routes: StaticRoutes
    bgp: Bgp
    sdwan_policy: SdwanPolicyManager
    vpn: SiteToSiteVpn
    traffic_shaping: TrafficShaping
    l3_firewall: L3Firewall
    l7_firewall: L7Firewall
    content_filtering: ContentFiltering
    appliance_nat: ApplianceNat
    security: ThreatPrevention
    uplinks: ApplianceUplinks
    lan: ApplianceVlans
    syslog: SyslogConfig

    model: str
    """Hardware model identifier (e.g. ``"MX250"``) — vendor-neutral metadata the
    driver resolves from its management API / inventory. The coverage axis for
    model-parameterised tests; read it here rather than reaching into a
    framework-specific config object."""


register_device_type("sdwan_appliance", SdwanApplianceDevice)
