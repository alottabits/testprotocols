"""WAN device archetypes — upstream-side server endpoints for end-to-end tests."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.conntrack import Conntrack
from testprotocols.devices import device_type
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
from testprotocols.nat import Nat
from testprotocols.nmap_scanner import NmapScanner
from testprotocols.ntp_client import NtpClient
from testprotocols.packet_filter import PacketFilter
from testprotocols.pcap_capture import PcapCapture
from testprotocols.snmp_client import SnmpClient


@runtime_checkable
class WanServerDevice(BaseDeviceProtocol, Protocol):
    """WAN server archetype — far-side host for end-to-end traffic and protocol tests.

    Sits on the WAN side of the topology to act as the remote endpoint for
    HTTP, DNS, iperf, NTP, and SNMP exchanges initiated from the LAN through a
    CPE / SD-WAN router under test. Includes L3 (IP, routing, DHCP, NAT,
    conntrack), packet capture, host packet-filtering, network scanning, and
    file transfer for orchestration of test artefacts.
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
    ntp_client: NtpClient
    nmap_scanner: NmapScanner
    file_transfer: FileTransfer
    snmp_client: SnmpClient
    packet_filter: PacketFilter
    nat: Nat
    conntrack: Conntrack


device_type("linux_wan_server", WanServerDevice)
