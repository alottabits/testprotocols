"""Networking data models for IP addresses and protocol results."""

from __future__ import annotations

import warnings
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from ipaddress import IPv4Address, IPv6Address
from typing import cast

from testprotocols.deprecation import MODEL_FRAMES, coerce_enum
from testprotocols.models import _checks
from testprotocols.models._open_enum import OpenEnumPair
from testprotocols.models._sync import settle
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


class DnsRecordType(StrEnum):
    """A DNS resource-record type (RFC 1035 and the IANA registry). Grows on evidence.

    The registry is open, and an answer can hold a type this enum does not name: a
    :class:`DnsRecord` read back holds ``OTHER`` and the type's own name in
    ``record_type_raw`` (shape 3o). ``OTHER`` is a read-back value only; a lookup for it is
    refused (``ValueError``).
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
    OTHER = "other"


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

    ``HTTPResult(response)`` takes the raw response text, as it always has (the
    parameter is named ``response``); :func:`parse_http_response` is the same parse as a
    function. *status* is the numeric status code, ``0`` when the response has none (an
    empty response, a status line without a numeric code, or a number outside 100 to 599);
    it will become ``int | None``. *body* is the text after the headers and *raw* the
    response as given.

    Equality is by value (*status*, *body* and *raw*); the released class compared by
    identity. The record is frozen. The released attributes still read: *code* is the status
    code as text (``""`` when absent) and *beautified_text* is *body*; each is
    deprecated, warns when read, and goes when the removal step is taken.
    """

    status: int
    body: str
    raw: str

    def __init__(self, response: str) -> None:
        if not isinstance(cast(object, response), str):
            raise TypeError(f"HTTPResult takes the response text, not {response!r}")
        code, body, _ = _split_response(response)
        object.__setattr__(self, "status", _status(code))
        object.__setattr__(self, "body", body)
        object.__setattr__(self, "raw", response)

    @property
    def code(self) -> str:
        """Deprecated: the status code as text; use *status*."""
        warnings.warn(
            "HTTPResult.code is deprecated; use HTTPResult.status",
            DeprecationWarning,
            skip_file_prefixes=MODEL_FRAMES,
        )
        return _split_response(self.raw)[0]

    @property
    def beautified_text(self) -> str:
        """Deprecated: the body; use *body*."""
        warnings.warn(
            "HTTPResult.beautified_text is deprecated; use HTTPResult.body",
            DeprecationWarning,
            skip_file_prefixes=MODEL_FRAMES,
        )
        return self.body

    @staticmethod
    def _parse_response(response: str) -> tuple[str, str, str]:
        """Deprecated: the (code, body, reason) split; kept for released callers."""
        return _split_response(response)


def _status(code: str) -> int:
    number = int(code) if code.isascii() and code.isdigit() else 0
    return number if 100 <= number <= 599 else 0


def parse_http_response(response: str) -> HTTPResult:
    """Parse the text of an HTTP response (status line, headers, body) into an HTTPResult."""
    return HTTPResult(response)


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


_DNS_PAIRS = (OpenEnumPair(DnsRecordType, DnsRecordType.OTHER, "record_type", "record_type_raw"),)


@dataclass(frozen=True)
class DnsRecord:
    """One resource record of a DNS answer: the owner *name* (as the resolver prints it,
    usually fully qualified with a trailing dot), its *record_type*, its *ttl* in seconds and
    its *data* (the record data as text: an address, a target name, ...).

    *record_type* is open (shape 3o): a type :class:`DnsRecordType` does not name is
    ``OTHER`` and its name is in *record_type_raw*, verbatim (``"CAA"``); *record_type_raw* is
    ``None`` otherwise, and a raw name beside a named type raises ``ValueError``. A plain
    string naming a member converts with a ``DeprecationWarning``; a driver reading device
    text builds the member itself (``DnsRecordType(word)``, ``OTHER`` and the word when that
    raises).
    """

    name: str
    record_type: DnsRecordType
    ttl: int
    data: str
    record_type_raw: str | None = None
    _record_type_seen: tuple[tuple[DnsRecordType | None, str | None], ...] | None = field(
        default=None, kw_only=True, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        _checks.text("DnsRecord", "name", self.name)
        _checks.count("DnsRecord", "ttl", self.ttl)
        _checks.text("DnsRecord", "data", self.data)
        settle(self, _DNS_PAIRS, "_record_type_seen")


@dataclass(frozen=True)
class PingResult:
    """The summary of an ICMP echo run: the *destination* as given, the echo requests
    *transmitted*, the distinct replies *received*, the *duplicates* among the replies, the
    *packet_loss_percent* (0 to 100) and the round-trip times in milliseconds (minimum,
    average, maximum and standard deviation; ``None`` when no reply came back).

    *received* is at most *transmitted*, and the loss agrees with them: within one percentage
    point of ``(transmitted - received) / transmitted * 100`` (the tool rounds it), and 0
    when nothing was transmitted. Anything else raises ``ValueError``."""

    destination: str
    transmitted: int
    received: int
    packet_loss_percent: float
    duplicates: int = 0
    rtt_min_ms: float | None = None
    rtt_avg_ms: float | None = None
    rtt_max_ms: float | None = None
    rtt_stddev_ms: float | None = None

    def __post_init__(self) -> None:
        _checks.text("PingResult", "destination", self.destination)
        for name in ("transmitted", "received", "duplicates"):
            _checks.count("PingResult", name, getattr(self, name))
        _checks.number("PingResult", "packet_loss_percent", self.packet_loss_percent, high=100)
        for name in ("rtt_min_ms", "rtt_avg_ms", "rtt_max_ms", "rtt_stddev_ms"):
            _checks.optional_number("PingResult", name, getattr(self, name))
        if self.received > self.transmitted:
            raise ValueError(
                f"PingResult.received ({self.received}) exceeds transmitted ({self.transmitted})"
            )
        expected = (
            0.0
            if self.transmitted == 0
            else (self.transmitted - self.received) / self.transmitted * 100
        )
        if abs(self.packet_loss_percent - expected) > 1:
            raise ValueError(
                f"PingResult.packet_loss_percent {self.packet_loss_percent} disagrees with "
                f"{self.received} of {self.transmitted} received"
            )


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
    """One scanned port: its number, transport *protocol*, *state* and the *service* name
    nmap guessed (``None`` when it named none). A plain string naming a member of
    :class:`~testprotocols.models.TransportProtocol` or :class:`NmapPortState` converts with a
    ``DeprecationWarning``; any other raises ``ValueError``."""

    port: int
    protocol: TransportProtocol
    state: NmapPortState
    service: str | None = None

    def __post_init__(self) -> None:
        _checks.count("NmapPort", "port", self.port)
        if not 1 <= self.port <= 65535:
            raise ValueError(f"NmapPort.port must be 1 to 65535: {self.port}")
        protocol = coerce_enum(
            TransportProtocol,
            cast("TransportProtocol | str", self.protocol),
            what="NmapPort.protocol",
            skip_file_prefixes=MODEL_FRAMES,
        )
        state = coerce_enum(
            NmapPortState,
            cast("NmapPortState | str", self.state),
            what="NmapPort.state",
            skip_file_prefixes=MODEL_FRAMES,
        )
        object.__setattr__(self, "protocol", protocol)
        object.__setattr__(self, "state", state)
        _checks.optional_text("NmapPort", "service", self.service)


@dataclass(frozen=True)
class NmapResult:
    """What a port scan found on its target: whether the host is *up*, the *addresses* nmap
    reported for it (as text, in report order) and the scanned *ports* in scan order. A list
    is accepted and held as a tuple."""

    up: bool
    addresses: tuple[str, ...] = ()
    ports: tuple[NmapPort, ...] = ()

    def __post_init__(self) -> None:
        _checks.flag("NmapResult", "up", self.up)
        object.__setattr__(
            self, "addresses", _checks.texts("NmapResult", "addresses", self.addresses)
        )
        ports = cast(object, self.ports)
        if not isinstance(ports, list | tuple):
            raise TypeError(f"NmapResult.ports takes a tuple of NmapPort, not {ports!r}")
        held: list[NmapPort] = []
        for item in cast("Sequence[object]", ports):
            if not isinstance(item, NmapPort):
                raise TypeError(f"NmapResult.ports holds NmapPort only, not {item!r}")
            held.append(item)
        object.__setattr__(self, "ports", tuple(held))


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

    def __post_init__(self) -> None:
        if not isinstance(cast(object, self.address), IPv4Address):
            raise TypeError(f"ArpEntry.address takes an IPv4Address, not {self.address!r}")
        for name in ("hw_type", "hw_address", "flags", "interface"):
            _checks.text("ArpEntry", name, getattr(self, name))
