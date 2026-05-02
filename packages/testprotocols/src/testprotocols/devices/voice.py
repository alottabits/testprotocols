"""Voice device archetypes — SIP phone and SIP server."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.devices import device_type
from testprotocols.dhcp_client import DhcpClient
from testprotocols.file_transfer import FileTransfer
from testprotocols.ip_interface import IpInterface
from testprotocols.pcap_capture import PcapCapture
from testprotocols.sip_phone import SipPhone
from testprotocols.sip_server import SipServer


@runtime_checkable
class SipPhoneDevice(Protocol):
    """SIP phone archetype — endpoint that registers with a SIP server and places calls.

    Used to drive call-control scenarios (register / invite / cancel / bye) and
    media-plane verification against a SIP server under test.
    """

    sip_phone: SipPhone
    ip_interface: IpInterface
    dhcp_client: DhcpClient


@runtime_checkable
class SipServerDevice(Protocol):
    """SIP server archetype — registrar / proxy for SIP phones in voice tests.

    Provides the server-side SIP surface plus packet capture and file transfer
    for inspecting and exporting signalling exchanges.
    """

    sip_server: SipServer
    pcap: PcapCapture
    file_transfer: FileTransfer


device_type("linux_sip_phone", SipPhoneDevice)
device_type("linux_sip_server", SipServerDevice)
