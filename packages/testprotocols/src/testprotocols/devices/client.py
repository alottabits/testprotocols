"""Client device archetypes — wired LAN, wireless LAN, and QoE measurement endpoints."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.arp_client import ArpClient
from testprotocols.devices import register_device_type
from testprotocols.devices.base import BaseDeviceProtocol
from testprotocols.dhcp_client import DhcpClient
from testprotocols.dns_client import DnsClient
from testprotocols.file_transfer import FileTransfer
from testprotocols.http_client import HttpClient
from testprotocols.http_server import HttpServer
from testprotocols.ip_interface import IpInterface
from testprotocols.ip_routing import IpRouting
from testprotocols.iperf_client import IperfClient
from testprotocols.iperf_server import IperfServer
from testprotocols.multicast_client import MulticastClient
from testprotocols.network_endpoint import NetworkEndpoint
from testprotocols.network_probe import NetworkProbe
from testprotocols.nmap_scanner import NmapScanner
from testprotocols.ntp_client import NtpClient
from testprotocols.packet_filter import PacketFilter
from testprotocols.pcap_capture import PcapCapture
from testprotocols.qoe_browser import QoeBrowser
from testprotocols.upnp_client import UpnpClient
from testprotocols.vlan_client import VlanClient
from testprotocols.wifi_client import WifiClient


@runtime_checkable
class LanClientDevice(BaseDeviceProtocol, Protocol):
    """Wired LAN client archetype — a host on the customer LAN segment.

    Used as a traffic source/sink and protocol endpoint for testing CPE/router
    behaviour from the subscriber side. Provides L3 (IP, routing, DHCP), the
    common application-layer clients (HTTP/DNS/iperf/UPnP/multicast/NTP/file
    transfer), packet capture, network scanning, host packet-filtering, and
    L2 helpers (ARP, VLAN tagging).
    """

    ip_interface: IpInterface
    ip_routing: IpRouting
    dhcp_client: DhcpClient
    http_client: HttpClient
    http_server: HttpServer
    dns_client: DnsClient
    iperf_client: IperfClient
    iperf_server: IperfServer
    pcap: PcapCapture
    upnp_client: UpnpClient
    multicast_client: MulticastClient
    ntp_client: NtpClient
    nmap_scanner: NmapScanner
    file_transfer: FileTransfer
    packet_filter: PacketFilter
    arp_client: ArpClient
    vlan_client: VlanClient
    network_probe: NetworkProbe
    data_plane_endpoint: NetworkEndpoint


@runtime_checkable
class WlanClientDevice(BaseDeviceProtocol, Protocol):
    """Wireless LAN client archetype — a Wi-Fi station for over-the-air testing.

    Used to drive Wi-Fi association, roaming, and traffic scenarios against a
    CPE / access point. Provides Wi-Fi client capabilities plus the L3 / app
    surface needed to exercise data-plane behaviour once associated.
    """

    wifi_client: WifiClient
    ip_interface: IpInterface
    ip_routing: IpRouting
    dhcp_client: DhcpClient
    http_client: HttpClient
    iperf_client: IperfClient
    iperf_server: IperfServer
    pcap: PcapCapture
    upnp_client: UpnpClient
    multicast_client: MulticastClient
    ntp_client: NtpClient
    nmap_scanner: NmapScanner
    file_transfer: FileTransfer


@runtime_checkable
class QoeClientDevice(BaseDeviceProtocol, Protocol):
    """QoE (Quality of Experience) client archetype — browser-driven measurement endpoint.

    Minimal client used to drive web-based QoE workloads (page load, video
    streaming) against test servers and through CPE/SD-WAN under test.
    """

    qoe_browser: QoeBrowser
    ip_interface: IpInterface
    dhcp_client: DhcpClient


register_device_type("linux_lan_client", LanClientDevice)
register_device_type("linux_wlan_client", WlanClientDevice)
register_device_type("linux_qoe_client", QoeClientDevice)
