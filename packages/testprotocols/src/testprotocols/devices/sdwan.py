"""SD-WAN device archetypes."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.conntrack import Conntrack
from testprotocols.devices import device_type
from testprotocols.ip_interface import IpInterface
from testprotocols.nat import Nat
from testprotocols.netem_controller import NetemController
from testprotocols.pcap_capture import PcapCapture
from testprotocols.router import Router
from testprotocols.sdwan_policy_manager import SdwanPolicyManager


@runtime_checkable
class SdwanRouterDevice(Protocol):
    """SD-WAN router archetype — branch / edge router with policy-based path selection.

    Combines a generic routing surface, SD-WAN policy management (path / app
    steering), traffic-impairment injection (netem) for emulating WAN
    conditions, IP interface management, packet capture, NAT, and connection
    tracking — the full set of L3 levers a test needs to exercise SD-WAN
    behaviour end to end.
    """

    routing: Router
    sdwan_policy: SdwanPolicyManager
    netem: NetemController
    ip_interface: IpInterface
    pcap: PcapCapture
    nat: Nat
    conntrack: Conntrack


device_type("linux_sdwan_router", SdwanRouterDevice)
