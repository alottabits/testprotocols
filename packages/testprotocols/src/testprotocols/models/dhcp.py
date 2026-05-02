"""DHCP and DHCPv6 packet trace data models."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from testprotocols.models.networking import IPAddresses


@dataclass
class DHCPTraceData:
    """Holds a captured DHCPv4 packet with source/destination addresses and message type."""

    source: IPAddresses
    destination: IPAddresses
    dhcp_packet: dict[str, Any]
    dhcp_message_type: int


@dataclass
class DHCPV6TraceData:
    """Holds a captured DHCPv6 packet with source/destination addresses and message type."""

    source: IPAddresses
    destination: IPAddresses
    dhcpv6_packet: dict[str, Any]
    dhcpv6_message_type: int
