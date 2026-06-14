"""Managed switch device archetypes — vendor-neutral.

``L2Switch`` is the managed access switch: the capability surface an
API/controller-managed switch exposes, satisfiable by any vendor's driver.
Host-substrate levers (conntrack, pcap, ip_interface, nat, packet_filter,
firewall_zones, wan_link_admin) are deliberately absent — a switch is not a Linux
host. See docs/l2-switch-protocol-design.md.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.devices import register_device_type
from testprotocols.devices.base import BaseDeviceProtocol
from testprotocols.discovery import Discovery
from testprotocols.first_hop_security import FirstHopSecurity
from testprotocols.link_aggregation import LinkAggregation
from testprotocols.mac_table import MacTable
from testprotocols.ntp_config import NtpConfig
from testprotocols.port_poe import PortPoe
from testprotocols.port_security import PortSecurity
from testprotocols.port_status import PortStatus
from testprotocols.radius_client import RadiusClient
from testprotocols.spanning_tree import SpanningTree
from testprotocols.storm_control import StormControl
from testprotocols.switch_acl import SwitchAcl
from testprotocols.switch_ports import SwitchPorts
from testprotocols.switch_qos import SwitchQos
from testprotocols.switch_vlans import SwitchVlans
from testprotocols.syslog_config import SyslogConfig


@runtime_checkable
class L2Switch(BaseDeviceProtocol, Protocol):
    """Managed access switch archetype — vendor-neutral.

    Composes the shared L2 capability layer. ``radius`` and ``syslog`` are reused
    as-is; ``first_hop_security`` and ``ntp`` are net-new baseline capabilities.
    The sibling ``L3Switch`` (separate doc) composes this set plus an L3 layer as
    a strict superset.
    """

    switch_ports: SwitchPorts
    switch_vlans: SwitchVlans
    spanning_tree: SpanningTree
    link_aggregation: LinkAggregation
    port_poe: PortPoe
    port_security: PortSecurity
    radius: RadiusClient
    first_hop_security: FirstHopSecurity
    storm_control: StormControl
    switch_acl: SwitchAcl
    discovery: Discovery
    mac_table: MacTable
    port_status: PortStatus
    switch_qos: SwitchQos
    syslog: SyslogConfig
    ntp: NtpConfig


register_device_type("managed_switch_l2", L2Switch)
