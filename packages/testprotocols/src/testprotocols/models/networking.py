"""Networking data models for IP addresses and protocol results."""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import IPv4Address, IPv6Address


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


class HTTPResult:
    """Parses and holds an HTTP response string, exposing the status code and body."""

    def __init__(self, response: str) -> None:
        self.raw = response
        self.code, self.beautified_text, _ = self._parse_response(response)

    @staticmethod
    def _parse_response(response: str) -> tuple[str, str, str]:
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
