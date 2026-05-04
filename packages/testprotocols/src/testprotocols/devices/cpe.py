"""CPE (Customer Premises Equipment) device archetype."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.conntrack import Conntrack
from testprotocols.device_lifecycle import DeviceLifecycle
from testprotocols.device_management import DeviceManagement
from testprotocols.devices import device_type
from testprotocols.devices.base import BaseDeviceProtocol
from testprotocols.firewall_zones import FirewallZones
from testprotocols.hw_console import HwConsole
from testprotocols.ip_interface import IpInterface
from testprotocols.ip_routing import IpRouting
from testprotocols.nat import Nat
from testprotocols.ntp_client import NtpClient
from testprotocols.packet_filter import PacketFilter
from testprotocols.port_forwarding import PortForwarding
from testprotocols.tr069_client import Tr069Client
from testprotocols.wifi_bss import WifiBss
from testprotocols.wifi_onboarding import WifiOnboarding
from testprotocols.wifi_radio import WifiRadio
from testprotocols.wifi_rf import WifiRf
from testprotocols.wifi_stations import WifiStations
from testprotocols.wifi_transitions import WifiTransitions


@runtime_checkable
class CpeDevice(BaseDeviceProtocol, Protocol):
    """CPE device archetype — black-box surface for residential / SMB gateways.

    Aggregates the capability protocols any conforming CPE driver must provide:
    TR-069 management, lifecycle, hardware console, the full Wi-Fi stack
    (radio / BSS / stations / RF / transitions / onboarding), L3 (IP, routing,
    NAT, port-forwarding), L2 packet filter + zone-based firewall, and NTP.

    Plugin-local extensions (richer levels, additional capabilities) can
    derive their own Protocol from this one.
    """

    tr069_client: Tr069Client
    device_management: DeviceManagement
    device_lifecycle: DeviceLifecycle
    hw_console: HwConsole
    wifi_radio: WifiRadio
    wifi_bss: WifiBss
    wifi_stations: WifiStations
    wifi_rf: WifiRf
    wifi_transitions: WifiTransitions
    wifi_onboarding: WifiOnboarding
    ip_interface: IpInterface
    ip_routing: IpRouting
    packet_filter: PacketFilter
    nat: Nat
    port_forwarding: PortForwarding
    conntrack: Conntrack
    firewall_zones: FirewallZones
    ntp_client: NtpClient


device_type("linux_cpe", CpeDevice)
