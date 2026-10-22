"""CPE gateway device archetype and its optional tiers — vendor-neutral.

``CpeGatewayDevice`` is the universal core of a residential or small-business
gateway as its management plane publishes it: the WAN connection, the LAN
(DHCP, DNS forwarder, bridges, hosts), Wi-Fi, the firewall, identity and health,
time, lifecycle, the local credential and TR-069. The two facets that fail the
core threshold or the class definition — the mesh controller and the USP agent —
are optional tier Protocols, each a strict superset of the core, so a driver
satisfies any combination of them; a third, voice, is staged until a majority of
the reviewed families publishes it. Design:
docs/architecture/cpe-gateway-protocol-design.md (§4, §6). It supersedes
``CpeDevice`` (registry key ``linux_cpe``), which stays registered for its
deprecation period.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.admin_credential import AdminCredential
from testprotocols.auto_port_mapping import AutoPortMapping
from testprotocols.device_health import DeviceHealth
from testprotocols.device_info import DeviceInfo
from testprotocols.device_lifecycle import DeviceLifecycle
from testprotocols.devices import register_device_type
from testprotocols.devices.base import BaseDeviceProtocol
from testprotocols.dhcp_client import DhcpClient
from testprotocols.dns_forwarder import DnsForwarder
from testprotocols.firewall import Firewall
from testprotocols.firewall_zones import FirewallZones
from testprotocols.host_filter import HostFilter
from testprotocols.host_table import HostTable
from testprotocols.interface_dhcp import InterfaceDhcp
from testprotocols.l2_bridge import L2Bridge
from testprotocols.network_endpoint import NetworkEndpoint
from testprotocols.ntp_config import NtpConfig
from testprotocols.port_status import PortStatus
from testprotocols.syslog_config import SyslogConfig
from testprotocols.tr069_client import Tr069Client
from testprotocols.usp_agent import UspAgent
from testprotocols.wan_connection import WanConnection
from testprotocols.wan_link_admin import WanLinkAdmin
from testprotocols.wifi_bss import WifiBss
from testprotocols.wifi_mesh import WifiMesh
from testprotocols.wifi_onboarding import WifiOnboarding
from testprotocols.wifi_radio import WifiRadio
from testprotocols.wifi_stations import WifiStations
from testprotocols.wifi_transitions import WifiTransitions


@runtime_checkable
class CpeGatewayDevice(BaseDeviceProtocol, Protocol):
    """CPE gateway — universal core. Vendor-neutral; satisfiable by any
    gateway whose driver publishes the members below. The reviewed
    families and their evidence are in
    docs/architecture/cpe-gateway-protocol-design.md (§2, §10); the
    management transport and who manages the device are driver concerns."""

    # NEW — the WAN connection as a managed object: mode, credentials, tag, IPv6, state
    wan_connection: WanConnection
    # reuse as-is — administrative down/up of the WAN by label; module docstring generalised
    wan_admin: WanLinkAdmin
    # reuse — release and renew of the WAN lease, v4 and v6
    dhcp_client: DhcpClient
    # reuse — link, speed, duplex of the WAN and LAN ports
    port_status: PortStatus
    # reuse as-is — pools, lease time, options, reservations, active leases
    interface_dhcp: InterfaceDhcp
    # NEW — upstreams, local host overrides, rebind protection
    dns_forwarder: DnsForwarder
    # NEW (GAPS 2026-05-02) — bridge membership of ports and wireless networks
    l2_bridge: L2Bridge
    # reuse — radios addressed by band; no band setter
    wifi_radio: WifiRadio
    # reuse — networks, security, visibility
    wifi_bss: WifiBss
    # reuse — attached stations, disconnect
    wifi_stations: WifiStations
    # EXTENDED — push-button and PIN as today; cancel and state read added
    wifi_onboarding: WifiOnboarding
    # reuse — 11k/v/r; band steering by composition
    wifi_transitions: WifiTransitions
    # reuse — zone defaults and membership; per-method unsupported on four columns
    firewall_zones: FirewallZones
    # reuse — port forwards and the DMZ host, plus the rule members it inherits
    firewall: Firewall
    # NEW — per-host block, on demand or on a weekly schedule
    host_filter: HostFilter
    # NEW — automatic port mapping enable per protocol; the mapping table
    auto_port_mapping: AutoPortMapping
    # NEW — the hosts behind the gateway: address, name, attachment
    hosts: HostTable
    # EXTENDED — model as today; manufacturer, serial number, OUI, hardware and software
    # version added
    info: DeviceInfo
    # NEW (split off DeviceManagement) — uptime, online state, load, memory, processes, log
    health: DeviceHealth
    # reuse — log export
    syslog: SyslogConfig
    # EXTENDED — servers as today; synchronisation state added
    ntp: NtpConfig
    # EXTENDED — boot wait, factory reset, reboot as today; firmware upgrade, configuration
    # export and import added; one member renamed
    device_lifecycle: DeviceLifecycle
    # NEW — the local administrator credential
    admin_credential: AdminCredential
    # EXTENDED — connection state, identifier and inform as today, the inform's meaning
    # stated; ACS configuration added
    tr069_client: Tr069Client
    # reuse — test-bed role object: the gateway's WAN-side address
    wan_endpoint: NetworkEndpoint
    # reuse — test-bed role object: the gateway's LAN-side address
    lan_endpoint: NetworkEndpoint


register_device_type("cpe_gateway", CpeGatewayDevice)


@runtime_checkable
class CpeGatewayMeshTier(CpeGatewayDevice, Protocol):
    """Adds the mesh-controller facet: the agents and their backhaul links,
    client steering between agents. The extender is not a device of this
    archetype; it is an agent in the controller's topology (§1). Evidence:
    three or four of five columns per operation (R56 to R58); the second
    trigger column publishes no controller, so its driver does not satisfy the
    tier. Not registered: a test pins against it with ``isinstance``."""

    # reuse (+ one defaulted field on the topology node) — topology, backhaul, steering
    wifi_mesh: WifiMesh


@runtime_checkable
class CpeGatewayUspTier(CpeGatewayDevice, Protocol):
    """Adds the USP agent: the controller endpoint and its transport, the
    agent's own endpoint identifier. Evidence: three of five columns (R53, all caveated); the
    second trigger column packages no agent, so its driver does not satisfy the
    tier. Not registered: a test pins against it with ``isinstance``."""

    # NEW (tier) — controller endpoint and transport, the agent's endpoint identifier
    usp_agent: UspAgent
