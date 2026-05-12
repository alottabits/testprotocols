"""Infrastructure device archetypes — ACS, provisioner, TFTP server."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.devices import register_device_type
from testprotocols.devices.base import BaseDeviceProtocol
from testprotocols.dhcp_server import DhcpServer
from testprotocols.file_transfer import FileTransfer
from testprotocols.packet_filter import PacketFilter
from testprotocols.pcap_capture import PcapCapture
from testprotocols.tftp_server import TftpServer
from testprotocols.tr069_server import Tr069Server


@runtime_checkable
class AcsDevice(BaseDeviceProtocol, Protocol):
    """ACS (Auto-Configuration Server) archetype — TR-069 server-side counterpart to CPE.

    Provides the TR-069 server protocol surface (CWMP plus ACS-side inventory
    and per-CPE connection status). Includes packet capture / filter and file
    transfer for diagnostic workflows. Drivers may implement the server
    surface over any transport (CWMP NBI, REST, GUI scrape); the choice is a
    driver-internal concern.
    """

    tr069_server: Tr069Server
    pcap: PcapCapture
    file_transfer: FileTransfer
    packet_filter: PacketFilter


@runtime_checkable
class ProvisionerDevice(BaseDeviceProtocol, Protocol):
    """Provisioner archetype — DHCP-driven device provisioning service.

    Hands out IP leases (with vendor-specific options) to CPEs and clients on
    the test network. Includes packet capture / filter and file transfer for
    inspecting provisioning exchanges.
    """

    dhcp_server: DhcpServer
    pcap: PcapCapture
    file_transfer: FileTransfer
    packet_filter: PacketFilter


@runtime_checkable
class TftpDevice(BaseDeviceProtocol, Protocol):
    """TFTP server archetype — file source for firmware downloads / config fetches.

    Minimal archetype used as a source for TR-069 ``Download`` operations and
    similar boot-time fetch flows.
    """

    tftp_server: TftpServer


register_device_type("linux_acs", AcsDevice)
register_device_type("linux_provisioner", ProvisionerDevice)
register_device_type("linux_tftp", TftpDevice)
