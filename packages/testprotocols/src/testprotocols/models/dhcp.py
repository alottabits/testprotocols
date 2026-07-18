"""DHCP and DHCPv6 packet trace data models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from testprotocols.models.networking import IPAddresses


@dataclass(frozen=True)
class DhcpLeaseObservation:
    """A DHCPv4 lease obtained as a scoped observation, with its received options.

    Produced by :meth:`testprotocols.dhcp_client.DhcpClient.observe_lease` —
    the lease a server granted to a client that explicitly requested a set of
    option codes, read from the client's own lease records (data-plane truth).

    The typed fields surface the core lease parameters. ``options`` carries the
    raw client-reported value string of every other option present in the
    lease, keyed by option code, exactly as the client recorded it — no
    normalization; value-comparison semantics belong to the caller.
    """

    address: str
    """The leased IPv4 address (dotted quad)."""

    subnet_mask: str = ""
    """Received subnet mask, option 1 (dotted quad; empty if absent)."""

    gateway: str = ""
    """First received router, option 3 (dotted quad; empty if absent)."""

    dns_servers: tuple[str, ...] = ()
    """Received DNS servers, option 6, in server order."""

    lease_time_s: int = 0
    """Received lease time in seconds, option 51 (0 if absent)."""

    server: str = ""
    """The DHCP server identifier, option 54 (dotted quad; empty if absent)."""

    options: Mapping[int, str] = field(default_factory=dict)
    """Raw received value per option code, as reported by the client."""


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
