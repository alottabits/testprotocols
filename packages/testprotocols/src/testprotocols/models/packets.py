"""Protocol-specific packet data models."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from ipaddress import IPv4Address, IPv4Interface, IPv6Interface


@dataclass
class RIPv2PacketData:
    """Holds fields extracted from a RIPv2 packet including source, destination, and route entries."""

    source: IPv4Address
    destination: IPv4Address
    ip_address: list[IPv4Address]
    subnet: list[IPv4Interface | IPv6Interface]
    frame_time: datetime | None = None
