"""Networking data models for IP addresses and protocol results."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from ipaddress import IPv4Address, IPv6Address
from typing import cast

from testprotocols.deprecation import MODEL_FRAMES


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
    """A DNS resource-record type (RFC 1035 and the IANA registry). Grows on evidence."""

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
