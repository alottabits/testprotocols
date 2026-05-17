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

    A phone has one or more SIP accounts (lines). Most testbeds run single-line
    phones; multi-line phones expose additional entries in ``aors``.

    ``aors`` is the list of registered SIP URIs in RFC 3261 §6 address-of-record
    form (``sip:user@host`` with optional ``;params``). ``host`` may be an FQDN,
    an IPv4 literal (``10.0.0.5``), or an IPv6 bracketed literal
    (``[2001:db8::5]``) — the driver decides which form matches its testbed's
    address-resolution context. The list is never empty; ``aors[0]`` is the
    primary line that single-line operations (``sip_phone.dial``,
    ``sip_phone.answer``, MWI subscriptions, …) act on.

    ``number`` is the user-part of ``aors[0]`` — the SIP phone's E.164 /
    dial-string identifier for its primary line. Provided as a convenience so
    single-line callers don't have to parse SIP URIs.

    ``device_name`` / ``device_type`` come from :class:`BaseDeviceProtocol`.
    """

    sip_phone: SipPhone
    ip_interface: IpInterface
    dhcp_client: DhcpClient
    number: str
    aors: list[str]


@runtime_checkable
class SipServerDevice(BaseDeviceProtocol, Protocol):
    """SIP server archetype — registrar / proxy for SIP phones in voice tests.

    Provides the server-side SIP surface plus packet capture and file transfer
    for inspecting and exporting signalling exchanges.

    ``aor_domain`` is the host part that callers should embed in SIP AORs
    targeting this server (``sip:user@<aor_domain>``). May be an FQDN, an
    IPv4 literal, or an IPv6 bracketed literal — the driver decides which
    form matches its testbed's address-resolution context.
    """

    sip_server: SipServer
    pcap: PcapCapture
    file_transfer: FileTransfer
    aor_domain: str


register_device_type("linux_sip_phone", SipPhoneDevice)
register_device_type("linux_sip_server", SipServerDevice)
