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

import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass


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


def main(argv: list[str]) -> int:
    """CLI entry point; filled in by the rules step."""
    del argv
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
