"""Networking data models for IP addresses and protocol results."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from enum import StrEnum
from ipaddress import IPv4Address, IPv6Address
from typing import cast

from testprotocols.deprecation import MODEL_FRAMES


class IpVersion(StrEnum):
    """An IP version, spelled as the host-tool parameters of the released contract spell it."""

    IPV4 = "ipv4"
    IPV6 = "ipv6"

    @property
    def number(self) -> int:
        """The version as the number the released ``int`` parameters carry: 4 or 6."""
        return 4 if self is IpVersion.IPV4 else 6


def coerce_ip_version(
    value: IpVersion | int | str | None,
    *,
    what: str,
    skip_file_prefixes: tuple[str, ...] = (),
) -> IpVersion | None:
    """Return *value* as an :class:`IpVersion`, or ``None`` for ``None``.

    For a driver's ``ip_version`` parameter, which was ``int | None`` (``4`` or ``6``):
    a member is returned as is; the number ``4`` or ``6`` (never a ``bool``) is the
    deprecated spelling, so it warns and returns the member; a plain ``str`` naming a
    member warns as :func:`~testprotocols.deprecation.coerce_enum` does. Any other number
    or string raises ``ValueError``; any other type raises ``TypeError``. The warning frame
    works as in ``coerce_enum``.
    """
    given = cast(object, value)
    if given is None or isinstance(given, IpVersion):
        return given
    if isinstance(given, bool) or not isinstance(given, (int, str)):
        raise TypeError(f"{what}: takes an IpVersion, 4, 6 or None, not {given!r}")
    member: IpVersion
    if isinstance(given, int):
        if given not in (4, 6):
            raise ValueError(f"{what}: {given!r} is not an IP version (4 or 6)")
        member = IpVersion.IPV4 if given == 4 else IpVersion.IPV6
        spelled = f"the number {given}"
    else:
        try:
            member = IpVersion(given)
        except ValueError:
            raise ValueError(
                f"{what}: {given!r} is not one of {[m.value for m in IpVersion]}"
            ) from None
        spelled = f"plain string {given!r}"
    warnings.warn(
        f"{what}: {spelled} is deprecated; pass IpVersion.{member.name}",
        DeprecationWarning,
        stacklevel=2 if skip_file_prefixes else 3,
        skip_file_prefixes=skip_file_prefixes,
    )
    return member


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
    empty response, or a status line without a numeric code); it will become
    ``int | None``. *body* is the text after the headers and *raw* the response as given.

    The record is frozen. The released attributes still read: *code* is the status
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
        object.__setattr__(self, "status", int(code) if code.isascii() and code.isdigit() else 0)
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
