"""Voice device archetypes — SIP phone and SIP server."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.devices import register_device_type
from testprotocols.devices.base import BaseDeviceProtocol
from testprotocols.dhcp_client import DhcpClient
from testprotocols.file_transfer import FileTransfer
from testprotocols.ip_interface import IpInterface
from testprotocols.pcap_capture import PcapCapture
from testprotocols.sip_phone import SipPhone
from testprotocols.sip_server import SipServer


@runtime_checkable
class SipPhoneDevice(BaseDeviceProtocol, Protocol):
    """SIP phone archetype — endpoint that registers with a SIP server and places calls.

    Used to drive call-control scenarios (register / invite / cancel / bye) and
    media-plane verification against a SIP server under test.

    ``number`` is the SIP phone's E.164 / dial-string identifier — promoted to
    the archetype because it's intrinsic to "I am a SIP phone" regardless of
    substrate, and because callers (operations, step defs) routinely need to
    address a phone by its number.

    ``device_name`` / ``device_type`` come from :class:`BaseDeviceProtocol`.
    """

    sip_phone: SipPhone
    ip_interface: IpInterface
    dhcp_client: DhcpClient
    number: str


@runtime_checkable
class SipServerDevice(BaseDeviceProtocol, Protocol):
    """SIP server archetype — registrar / proxy for SIP phones in voice tests.

    Provides the server-side SIP surface plus packet capture and file transfer
    for inspecting and exporting signalling exchanges.
    """

    sip_server: SipServer
    pcap: PcapCapture
    file_transfer: FileTransfer


register_device_type("linux_sip_phone", SipPhoneDevice)
register_device_type("linux_sip_server", SipServerDevice)
