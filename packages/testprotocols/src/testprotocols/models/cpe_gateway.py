"""CPE gateway records and vocabularies: the WAN connection, the DNS forwarder, the bridge,
the host table, host filtering, automatic port mapping and the USP agent (design §6).

Every record is frozen; every closed set is a ``StrEnum`` whose values are the lower-case
form of the member names, except ``Weekday``, an ``IntEnum`` with ISO numbering. A field
typed ``X | None`` states what its absence means in the record's docstring. Vendor neutrality
is part of the contract: no product name appears in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from enum import IntEnum, StrEnum

from testprotocols.models.firewall import PortMappingProtocol
from testprotocols.models.l2_common import StpMode, StpPortState

# --- The WAN connection -----------------------------------------------------------------


class WanMode(StrEnum):
    """How the WAN connection obtains its address: a lease, a static assignment or a PPPoE
    session. IPoE on a tagged uplink is ``DHCP`` or ``STATIC`` with the ``vlan`` part set."""

    DHCP = "dhcp"
    STATIC = "static"
    PPPOE = "pppoe"


class WanIpv6Mode(StrEnum):
    """How the connection obtains its IPv6 address and prefix, or ``DISABLED``."""

    DISABLED = "disabled"
    DHCPV6_PD = "dhcpv6_pd"
    SLAAC = "slaac"
    STATIC = "static"


class WanStatus(StrEnum):
    """The connection's status, the TR-181 connection-status set; a family with its own
    words maps them onto this set."""

    UNCONFIGURED = "unconfigured"
    CONNECTING = "connecting"
    AUTHENTICATING = "authenticating"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"


class ProvisioningMode(StrEnum):
    """Which address families the connection is provisioned for."""

    IPV4 = "ipv4"
    IPV6 = "ipv6"
    DUAL_STACK = "dual_stack"


@dataclass(frozen=True)
class PppoeCredentials:
    """The PPPoE session's credentials. *password* is required on a write and ``None`` on
    every read: no family returns a stored secret, and the written value is confirmed by the
    session reaching ``WanStatus.CONNECTED``. *service_name* is ``None`` when the session
    accepts any access concentrator's service."""

    username: str
    password: str | None
    service_name: str | None = None


@dataclass(frozen=True)
class StaticAddressing:
    """The static assignment: *address*, *prefix_length* and *gateway* are required;
    *dns_servers* are the resolvers the connection supplies in place of a lease's, empty when
    the forwarder's own upstreams are to serve."""

    address: str
    prefix_length: int
    gateway: str
    dns_servers: tuple[str, ...] = ()


@dataclass(frozen=True)
class WanVlan:
    """The tag the uplink carries; *priority* is ``None`` when no priority is set."""

    vlan_id: int
    priority: int | None = None


@dataclass(frozen=True)
class WanIpv6:
    """The connection's IPv6 part. *requested_prefix_length* is ``None`` unless the mode
    delegates a prefix and a length is requested; *static_address* is ``None`` unless the mode
    is ``STATIC``."""

    mode: WanIpv6Mode
    requested_prefix_length: int | None = None
    static_address: str | None = None


@dataclass(frozen=True)
class WanConnectionConfig:
    """One WAN connection: its *name* (the label ``wan_admin`` takes too), its *mode* and the
    mode-specific parts. A part that does not apply to the mode is ``None``; a configuration
    whose parts contradict its mode is rejected before any write."""

    name: str
    mode: WanMode
    pppoe: PppoeCredentials | None = None
    static: StaticAddressing | None = None
    vlan: WanVlan | None = None
    ipv6: WanIpv6 | None = None


@dataclass(frozen=True)
class WanConnectionState:
    """The connection's observed state, always filled by a read.

    Each address is ``None``, and *dns_servers* empty, while its address family is not
    provisioned or *status* is anything but ``CONNECTED``. *dns_servers* are the resolvers the
    connection supplies (a lease's or ``StaticAddressing.dns_servers``), not the forwarder's
    configured upstreams. *lease_remaining_s* is ``None`` where the family publishes no lease
    time; *provisioning_mode* is ``None`` only while neither family of addresses is up;
    *uptime_s* is ``None`` where the family publishes no connection uptime.
    """

    status: WanStatus
    ipv4_address: str | None
    ipv4_gateway: str | None
    dns_servers: tuple[str, ...]
    lease_remaining_s: int | None
    ipv6_address: str | None
    delegated_prefix: str | None
    provisioning_mode: ProvisioningMode | None
    uptime_s: int | None


# --- The DNS forwarder --------------------------------------------------------------------


@dataclass(frozen=True)
class DnsUpstream:
    """One configured upstream of the forwarder. *domain* names the suffix the upstream
    serves; ``None`` is the default upstream for every name."""

    address: str
    port: int = 53
    domain: str | None = None


@dataclass(frozen=True)
class DnsHostOverride:
    """One name the forwarder answers itself with *address*."""

    name: str
    address: str


# --- The bridge ---------------------------------------------------------------------------


class BridgeMemberKind(StrEnum):
    """What kind of interface a bridge member is."""

    PORT = "port"
    WIRELESS_NETWORK = "wireless_network"


@dataclass(frozen=True)
class BridgeMember:
    """One bridge member by *name* and *kind*."""

    name: str
    kind: BridgeMemberKind


@dataclass(frozen=True)
class BridgeConfig:
    """One bridge. *stp_mode* is ``None`` when spanning tree is off (the shared ``StpMode``
    has no off value). The record carries no membership and no address: ``add_member`` and
    ``remove_member`` own membership, ``interface_dhcp`` owns the address on the bridge."""

    name: str
    stp_mode: StpMode | None = None


@dataclass(frozen=True)
class BridgeMemberState:
    """One member's observed state; *stp_state* and *link_up* are each ``None`` where the
    family publishes no such state."""

    member: BridgeMember
    stp_state: StpPortState | None
    link_up: bool | None


# --- The host table -----------------------------------------------------------------------


class HostAttachment(StrEnum):
    """How a host attaches to the gateway. The set is closed by the contract: a host on a
    medium the set lacks reads ``None``."""

    ETHERNET = "ethernet"
    WIFI = "wifi"


@dataclass(frozen=True)
class LanHost:
    """One host the gateway knows. *mac* is the canonical lowercase colon-separated form.
    *ipv4_address* and *hostname* are ``None`` where the host has none the gateway knows;
    *attachment* is ``None`` where the family does not publish how the host attaches, or the
    medium is outside the set; *interface* is ``None`` where the family publishes no interface.
    """

    mac: str
    ipv4_address: str | None
    ipv6_addresses: tuple[str, ...]
    hostname: str | None
    attachment: HostAttachment | None
    interface: str | None
    active: bool


# --- Host filtering -----------------------------------------------------------------------


class Weekday(IntEnum):
    """A day of the week, ISO numbered (Monday is 1, Sunday is 7)."""

    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


@dataclass(frozen=True)
class WeeklySchedule:
    """The days and the daily window a block applies on; an *end* before *start* runs past
    midnight."""

    days: frozenset[Weekday]
    start: time
    end: time


@dataclass(frozen=True)
class HostBlock:
    """A per-host block of traffic through the gateway. *mac* is the canonical lowercase
    colon-separated form; *schedule* is ``None`` for a block that applies at all times."""

    mac: str
    schedule: WeeklySchedule | None = None
    enabled: bool = True


# --- Automatic port mapping ---------------------------------------------------------------


class AutoMappingProtocol(StrEnum):
    """A protocol by which a LAN host requests its own port mapping."""

    UPNP_IGD = "upnp_igd"
    PCP = "pcp"
    NAT_PMP = "nat_pmp"


@dataclass(frozen=True)
class AutoPortMappingEntry:
    """One mapping a LAN host requested. *origin* is ``None`` where the family does not say
    which protocol created the mapping; *remaining_lease_s* is ``None`` for a mapping without
    a lease or where the family publishes none; *description* is ``None`` where the host gave
    none."""

    external_port: int
    protocol: PortMappingProtocol
    internal_host: str
    internal_port: int
    origin: AutoMappingProtocol | None
    remaining_lease_s: int | None
    description: str | None


# --- The USP agent ------------------------------------------------------------------------


class UspTransport(StrEnum):
    """The message transport between the USP agent and its controller."""

    WEBSOCKET = "websocket"
    MQTT = "mqtt"
    STOMP = "stomp"


@dataclass(frozen=True)
class UspController:
    """The controller the USP agent connects to. *path* is the WebSocket resource path and
    ``None`` on the other transports, which have none."""

    endpoint_id: str
    transport: UspTransport
    host: str
    port: int
    path: str | None
    tls: bool


@dataclass(frozen=True)
class UspAgentState:
    """The agent's own *endpoint_id* and whether it is *connected* to its controller;
    ``None`` where the family publishes the configuration but no connection state."""

    endpoint_id: str
    connected: bool | None
