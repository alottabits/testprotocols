"""Neutrality pattern scan over a unified diff.

Reads a unified diff, looks only at added lines, and reports literals that
must not enter this public repository: IP addresses outside the
documentation ranges (RFC 1918 and the benchmarking range are tolerated
under a ``tests/`` directory), hostnames under private-use suffixes,
e-mail addresses outside the example domains, and ticket identifiers.

The script carries no organisation, customer or person names: a denylist
of names in a public repository would itself be the leak. The semantic
check (is this a customer's site, is this a person) belongs to the
reviewers; see CONTRIBUTING.md.

Usage: ``python scripts/neutrality_scan.py [DIFF_FILE]``; the diff is read
from stdin when no file is given. Exit status 1 when there is a hit.
"""

from __future__ import annotations

import ipaddress
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass(frozen=True)
class AddedLine:
    """One ``+`` line of a unified diff, located in the post-image file."""

    path: str
    line_no: int
    text: str


_FILE_HEADER = re.compile(r"^\+\+\+ (?:b/)?(.+)$")
_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def added_lines(diff: str) -> Iterator[AddedLine]:
    """Yield every added line of *diff* with its post-image path and line number."""
    path: str | None = None
    line_no = 0
    previous = ""
    for raw in diff.splitlines():
        header = _FILE_HEADER.match(raw)
        # A `+++ ` line is a file header only right after its `--- ` partner;
        # anywhere else it is an added line whose content starts with `++ `.
        if header is not None and previous.startswith("--- "):
            target = header.group(1)
            path = None if target == "/dev/null" else target
            previous = raw
            continue
        previous = raw
        hunk = _HUNK_HEADER.match(raw)
        if hunk is not None:
            line_no = int(hunk.group(1))
            continue
        if path is None or not raw:
            continue
        marker, text = raw[0], raw[1:]
        if marker == "+":
            yield AddedLine(path, line_no, text)
            line_no += 1
        elif marker == " ":
            line_no += 1


@dataclass(frozen=True)
class Hit:
    """A literal that must not enter the repository, and where it was added."""

    path: str
    line_no: int
    kind: str
    token: str


# RFC 5737 TEST-NET-1/2/3 and RFC 3849: allowed everywhere.
DOCUMENTATION_NETWORKS = (
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("2001:db8::/32"),
)
# RFC 1918 and the RFC 2544 benchmarking range: allowed under a tests/ directory only.
TEST_ONLY_NETWORKS = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
)
# RFC 2606 example domains plus the project owner's domain, which the package
# metadata already publishes.
ALLOWED_EMAIL_DOMAINS = frozenset({"example.com", "example.org", "example.net", "alottabits.com"})
# Traceability keys and standards-body identifiers that look like ticket ids.
ALLOWED_TICKET_PREFIXES = frozenset(
    {"UC", "ENG", "TR", "RFC", "ISO", "IEEE", "ITU", "UTF", "SHA", "AES", "TLS", "HTTP"}
)

_IPV4 = re.compile(r"(?<![\w.])(\d{1,3}(?:\.\d{1,3}){3})(?!\w|\.\d)")
_IPV6 = re.compile(r"(?<![\w:.])((?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4})(?![\w:])")
# A hostname counts only when delimited like a value (quotes, backticks,
# whitespace, URL separators), so `device.lan` attribute access in code does
# not trip it.
_HOSTNAME = re.compile(
    r"(?:^|(?<=[\s\"'`/@]))"
    r"((?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+(?:local|lan|internal))"
    r"(?=$|[\s\"'`/:])(?!\s*=)",
    re.IGNORECASE,
)
_EMAIL = re.compile(r"[\w.+-]+@((?:[\w-]+\.)+[A-Za-z]{2,})")
_TICKET = re.compile(r"(?<![\w-])([A-Z]{2,})-\d+\b")


def _is_test_path(path: str) -> bool:
    return "tests" in PurePosixPath(path).parts


def _address_allowed(address: ipaddress.IPv4Address | ipaddress.IPv6Address, path: str) -> bool:
    if (
        address.is_unspecified
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
    ):
        return True
    if any(address in network for network in DOCUMENTATION_NETWORKS):
        return True
    return _is_test_path(path) and any(address in network for network in TEST_ONLY_NETWORKS)


def _ip_hits(path: str, text: str) -> list[tuple[str, str]]:
    hits: list[tuple[str, str]] = []
    for pattern in (_IPV4, _IPV6):
        for match in pattern.finditer(text):
            token = match.group(1)
            try:
                address = ipaddress.ip_address(token)
            except ValueError:
                continue
            if not _address_allowed(address, path):
                hits.append(("ip-literal", token))
    return hits


def _hostname_hits(text: str) -> list[tuple[str, str]]:
    return [("hostname", m.group(1)) for m in _HOSTNAME.finditer(text)]


def _email_hits(text: str) -> list[tuple[str, str]]:
    if text.lstrip().startswith("Signed-off-by:"):
        return []
    return [
        ("email", m.group(0))
        for m in _EMAIL.finditer(text)
        if m.group(1).lower() not in ALLOWED_EMAIL_DOMAINS
    ]


def _ticket_hits(text: str) -> list[tuple[str, str]]:
    return [
        ("ticket-id", m.group(0))
        for m in _TICKET.finditer(text)
        if m.group(1) not in ALLOWED_TICKET_PREFIXES
    ]


def check_line(path: str, text: str) -> list[tuple[str, str]]:
    """Every ``(kind, token)`` in *text* that the rules reject, given its file *path*."""
    return _ip_hits(path, text) + _hostname_hits(text) + _email_hits(text) + _ticket_hits(text)


def scan_diff(diff: str) -> list[Hit]:
    """All hits over the added lines of *diff*, in diff order."""
    return [
        Hit(line.path, line.line_no, kind, token)
        for line in added_lines(diff)
        for kind, token in check_line(line.path, line.text)
    ]


def main(argv: list[str]) -> int:
    diff = Path(argv[0]).read_text() if argv else sys.stdin.read()
    hits = scan_diff(diff)
    for hit in hits:
        print(f"{hit.path}:{hit.line_no}: {hit.kind}: {hit.token}")
    if hits:
        print(f"\n{len(hits)} neutrality hit(s). See CONTRIBUTING.md, section Neutrality.")
        return 1
    print("neutrality scan: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
