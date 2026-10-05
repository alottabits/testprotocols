"""Networking data models for IP addresses and protocol results."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum
from ipaddress import IPv4Address, IPv6Address

from testprotocols._compat import deprecated
from testprotocols.models.traffic import TransportProtocol


class IpVersion(StrEnum):
    """An IP version as text, ``ipv4`` or ``ipv6``: the word ``NmapScanner.nmap`` takes for
    ``ip_type``. (The numeric spellings are :class:`IpFamily`.)"""

    IPV4 = "ipv4"
    IPV6 = "ipv6"


class IpFamily(IntEnum):
    """An IP version as the number the host-tool ``ip_version`` parameters carry (the
    iperf options and, as text, the HTTP server option). Being an ``int``, a member
    formats as ``4`` or ``6`` and compares equal to the number."""

    V4 = 4
    V6 = 6


class SnmpValueType(StrEnum):
    """The SNMP value type (RFC 2578 base types) of the value an SNMP SET writes.

    A driver maps each member to its tool's own type code. The members are the types a SET
    can carry: Counter32 and Counter64 are left out because a counter only ever increments
    (RFC 2578, sections 7.1.6 and 7.1.10), so no object accepts a SET of one, and Opaque is
    obsolete. A value beginning ``0x`` is sent as hex; hex is an input notation, not a type.
    """

    INTEGER = "integer"
    """INTEGER / Integer32."""
    UNSIGNED = "unsigned"
    """Unsigned32 (Gauge32)."""
    OCTET_STRING = "octet-string"
    """OCTET STRING."""
    OBJECT_IDENTIFIER = "object-identifier"
    """OBJECT IDENTIFIER."""
    IP_ADDRESS = "ip-address"
    """IpAddress."""
    TIMETICKS = "timeticks"
    """TimeTicks."""
    BITS = "bits"
    """BITS (the textual construct of RFC 2578, section 7.1.4, carried as an octet string)."""


class DnsRecordType(StrEnum):
    """A DNS resource-record type (RFC 1035 and the IANA registry). Grows on evidence.

    The registry is open: an answer can hold a type this enum does not name, and
    :attr:`DnsRecord.record_type` carries the resolver's own word as text.
    """

    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"
    NS = "NS"
    PTR = "PTR"
    SOA = "SOA"
    SRV = "SRV"
    TXT = "TXT"


class HttpScheme(StrEnum):
    """The URL scheme a request is made with."""

    HTTP = "http"
    HTTPS = "https"


class LinkAdminState(StrEnum):
    """The administrative state a host interface is set to (``ip link set <if> up|down``).

    Not :class:`~testprotocols.models.PortAdminState`: a switch port is ``enabled`` or
    ``disabled``, a host interface is set ``up`` or ``down``, and the released words are those.
    """

    UP = "up"
    DOWN = "down"


@dataclass
class IPAddresses:
    """Holds optional IPv4, IPv6, and link-local IPv6 addresses for a network endpoint."""

    ipv4: IPv4Address | None
    ipv6: IPv6Address | None
    link_local_ipv6: IPv6Address | None


@dataclass
class ICMPPacketData:
    """Holds ICMP packet fields including query code and source/destination addresses."""

    query_code: int
    source: IPAddresses
    destination: IPAddresses


@dataclass(frozen=True, init=False)
class HTTPResult:
    """An HTTP response parsed from its text: the status code, the body and the raw text.

    ``HTTPResult(response)`` takes the raw response text, as it always has (the parameter is named
    ``response``). *status* is the numeric status code, ``0`` when the response has none (an empty
    response, a status line without a numeric code, or a number outside 100 to 599); it will become
    ``int | None``. *body* is the text after the headers and *raw* the response as given.

    Equality is by value (*status*, *body* and *raw*); the released class compared by
    identity. The record is frozen. The released attributes still read: *code* is the status
    code as text (``""`` when absent) and *beautified_text* is *body*; each is deprecated.
    """

    status: int
    body: str
    raw: str

    def __init__(self, response: str) -> None:
        code, body, _ = _split_response(response)
        object.__setattr__(self, "status", _status(code))
        object.__setattr__(self, "body", body)
        object.__setattr__(self, "raw", response)

    @property
    @deprecated(
        "Deprecated: use status. Removal not before the first release 6 months after the "
        "release that deprecates it.",
        category=None,
    )
    def code(self) -> str:
        """The status code as text (``""`` when absent).

        Deprecated: use *status*. Removal not before the first release 6 months after the
        release that deprecates it.
        """
        return _split_response(self.raw)[0]

    @property
    @deprecated(
        "Deprecated: use body. Removal not before the first release 6 months after the "
        "release that deprecates it.",
        category=None,
    )
    def beautified_text(self) -> str:
        """The body.

        Deprecated: use *body*. Removal not before the first release 6 months after the
        release that deprecates it.
        """
        return self.body

    @staticmethod
    def _parse_response(response: str) -> tuple[str, str, str]:
        """The released (code, body, reason) split."""
        return _split_response(response)


def _status(code: str) -> int:
    number = int(code) if code.isascii() and code.isdigit() else 0
    return number if 100 <= number <= 599 else 0


def _split_response(response: str) -> tuple[str, str, str]:
    lines = response.split("\r\n", 1) if "\r\n" in response else response.split("\n", 1)
    status_line = lines[0] if lines else ""
    parts = status_line.split(" ", 2)
    code = parts[1] if len(parts) > 1 else ""
    reason = parts[2] if len(parts) > 2 else ""
    body = lines[1] if len(lines) > 1 else ""
    if "\r\n\r\n" in body:
        body = body.split("\r\n\r\n", 1)[1]
    elif "\n\n" in body:
        body = body.split("\n\n", 1)[1]
    elif body.startswith("\r\n"):
        body = body[2:]
    elif body.startswith("\n"):
        body = body[1:]
    return code, body, reason


@dataclass(frozen=True)
class DnsRecord:
    """One resource record of a DNS answer: the owner *name* (as the resolver prints it,
    usually fully qualified with a trailing dot), its *record_type*, its *ttl* in seconds and
    its *data* (the record data as text: an address, a target name, ...). *ttl* is not
    negative.

    *record_type* is the resolver's own word, stored as given (``"A"``, ``"CAA"``); the common
    ones are the values of :class:`DnsRecordType`.
    """

    name: str
    record_type: str
    ttl: int
    data: str


@dataclass(frozen=True)
class PingResult:
    """The summary of an ICMP echo run: the *destination* as given, the echo requests
    *transmitted*, the distinct replies *received*, the *duplicates* among the replies, the
    *packet_loss_percent* (0 to 100) and the round-trip times in milliseconds (minimum,
    average, maximum and standard deviation; ``None`` when no reply came back).

    The counts and times are not negative and finite. *received* is at most *transmitted*,
    and the loss agrees with them: within one percentage point of
    ``(transmitted - received) / transmitted * 100`` (the tool rounds it), and 0 when nothing
    was transmitted."""

    destination: str
    transmitted: int
    received: int
    packet_loss_percent: float
    duplicates: int = 0
    rtt_min_ms: float | None = None
    rtt_avg_ms: float | None = None
    rtt_max_ms: float | None = None
    rtt_stddev_ms: float | None = None


class NmapPortState(StrEnum):
    """A port state as nmap reports it (its six documented states)."""

    OPEN = "open"
    CLOSED = "closed"
    FILTERED = "filtered"
    UNFILTERED = "unfiltered"
    OPEN_FILTERED = "open|filtered"
    CLOSED_FILTERED = "closed|filtered"


@dataclass(frozen=True)
class NmapPort:
    """One scanned port: its number (1 to 65535), transport *protocol*, *state* and the
    *service* name nmap guessed (``None`` when it named none)."""

    port: int
    protocol: TransportProtocol
    state: NmapPortState
    service: str | None = None


@dataclass(frozen=True)
class NmapResult:
    """What a port scan found on its target: whether the host is *up*, the *addresses* nmap
    reported for it (as text, in report order) and the scanned *ports* in scan order."""

    up: bool
    addresses: tuple[str, ...] = ()
    ports: tuple[NmapPort, ...] = ()


@dataclass(frozen=True)
class ArpEntry:
    """One complete entry of a host's ARP table (IPv4 neighbours): the neighbour's
    *address*, the hardware type (*hw_type*, ``"ether"``), its hardware address
    (*hw_address*, as the host prints it), the entry *flags* (``"C"`` complete, ``"M"``
    permanent, ``"P"`` published) and the *interface* it was learnt on."""

    address: IPv4Address
    hw_type: str
    hw_address: str
    flags: str
    interface: str
