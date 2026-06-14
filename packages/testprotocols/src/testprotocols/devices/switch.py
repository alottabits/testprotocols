"""Managed switch device archetypes — vendor-neutral.

``L2Switch`` is the managed access switch: the capability surface an
API/controller-managed switch exposes, satisfiable by any vendor's driver.
Host-substrate levers (conntrack, pcap, ip_interface, nat, packet_filter,
firewall_zones, wan_admin) are deliberately absent — a switch is not a Linux
host. See docs/l2-switch-protocol-design.md.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.bgp import Bgp
from testprotocols.devices import register_device_type
from testprotocols.devices.base import BaseDeviceProtocol
from testprotocols.discovery import Discovery
from testprotocols.first_hop_security import FirstHopSecurity
from testprotocols.gateway_redundancy import GatewayRedundancy
from testprotocols.interface_dhcp import InterfaceDhcp
from testprotocols.link_aggregation import LinkAggregation
from testprotocols.mac_table import MacTable
from testprotocols.ntp_config import NtpConfig
from testprotocols.ospf import Ospf
from testprotocols.port_poe import PortPoe
from testprotocols.port_security import PortSecurity
from testprotocols.port_status import PortStatus
from testprotocols.radius_client import RadiusClient
from testprotocols.routed_interfaces import RoutedInterfaces
from testprotocols.routing_read import RoutingRead
from testprotocols.spanning_tree import SpanningTree
from testprotocols.static_routes import StaticRoutes
from testprotocols.storm_control import StormControl
from testprotocols.switch_acl import SwitchAcl
from testprotocols.switch_ports import SwitchPorts
from testprotocols.switch_qos import SwitchQos
from testprotocols.switch_vlans import SwitchVlans
from testprotocols.syslog_config import SyslogConfig


@runtime_checkable
class L2Switch(BaseDeviceProtocol, Protocol):
    """Managed access switch archetype — vendor-neutral.

    Composes the shared L2 capability layer. ``radius`` and ``syslog`` are reused
    as-is; ``first_hop_security`` and ``ntp`` are net-new baseline capabilities.
    The sibling ``L3Switch`` (separate doc) composes this set plus an L3 layer as
    a strict superset.
    Host-substrate levers (conntrack, pcap, ip_interface, nat, packet_filter,
    firewall_zones, wan_admin) are deliberately absent — a switch is API/controller-managed,
    not a Linux host.
    """

    switch_ports: SwitchPorts
    switch_vlans: SwitchVlans
    spanning_tree: SpanningTree
    link_aggregation: LinkAggregation
    port_poe: PortPoe
    port_security: PortSecurity
    radius: RadiusClient
    first_hop_security: FirstHopSecurity
    storm_control: StormControl
    switch_acl: SwitchAcl
    discovery: Discovery
    mac_table: MacTable
    port_status: PortStatus
    switch_qos: SwitchQos
    syslog: SyslogConfig
    ntp: NtpConfig


register_device_type("managed_switch_l2", L2Switch)


@runtime_checkable
class L3Switch(L2Switch, Protocol):
    """Managed distribution switch — strict superset of L2Switch plus an L3 layer.

    Inherits the full L2 capability layer via Protocol inheritance and adds
    routed interfaces, static routes, RIB read, OSPF, per-interface DHCP, and
    gateway redundancy. Scope is the default VRF (multi-VRF deferred, GAPS.md).
    BGP is on the L3SwitchRouted tier (it fails the L3 majority bar).
    Host-substrate levers (conntrack, pcap, ip_interface, nat, packet_filter,
    firewall_zones, wan_admin) are deliberately absent — same exclusion as
    ``L2Switch``. The WAN-edge uplink-admin surface (``wan_admin`` / full
    ``Router`` write layer) is also excluded: an API-managed switch cannot
    admin-down its own uplinks, so the RIB surface here is the read-only
    ``routing_read`` / ``RouteEntry`` view, not the router's write surface.
    """

    routed_interfaces: RoutedInterfaces
    static_routes: StaticRoutes
    routing_read: RoutingRead
    ospf: Ospf
    interface_dhcp: InterfaceDhcp
    gateway_redundancy: GatewayRedundancy


register_device_type("managed_switch_l3", L3Switch)


@runtime_checkable
class L3SwitchRouted(L3Switch, Protocol):
    """L3Switch plus BGP — the routed-distribution tier.

    BGP is absent on the cloud design-target and fails the L3 majority bar, so it
    is a separate tier rather than a mandatory L3Switch attribute. A driver for a
    BGP-capable switch satisfies this; the registration isinstance-gate flags a
    missing bgp at startup.
    """

    bgp: Bgp


register_device_type("managed_switch_l3_routed", L3SwitchRouted)
