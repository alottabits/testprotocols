"""testprotocols — capability and device Protocols for telco resources under test."""

__version__ = "0.1.0"

from testprotocols.devices.client import (
    LanClientDevice,
    QoeClientDevice,
    WlanClientDevice,
)
from testprotocols.devices.cpe import CpeDevice
from testprotocols.devices.infra import (
    AcsDevice,
    ProvisionerDevice,
    TftpDevice,
)
from testprotocols.devices.sdwan import SdwanRouterDevice
from testprotocols.devices.traffic import (
    IperfTrafficGeneratorDevice,
    TrafficControllerDevice,
)
from testprotocols.devices.voice import (
    SipPhoneDevice,
    SipServerDevice,
)
from testprotocols.devices.wan import WanServerDevice
from testprotocols.firewall_zones import FirewallZones
from testprotocols.ip_interface import IpInterface
from testprotocols.ip_routing import IpRouting
from testprotocols.netem_controller import NetemController
from testprotocols.sip_phone import SipPhone
from testprotocols.sip_server import SipServer
from testprotocols.tr069_client import Tr069Client
from testprotocols.tr069_server import Tr069Server

__all__ = [
    "AcsDevice",
    "CpeDevice",
    "FirewallZones",
    "IpInterface",
    "IpRouting",
    "IperfTrafficGeneratorDevice",
    "LanClientDevice",
    "NetemController",
    "ProvisionerDevice",
    "QoeClientDevice",
    "SdwanRouterDevice",
    "SipPhone",
    "SipPhoneDevice",
    "SipServer",
    "SipServerDevice",
    "TftpDevice",
    "Tr069Client",
    "Tr069Server",
    "TrafficControllerDevice",
    "WanServerDevice",
    "WlanClientDevice",
]
