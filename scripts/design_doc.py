"""Archetype design documents (docs/archetypes/README.md, "The design document").

Pure readers over a design document's text: its Status, its numbered
sections and its landing-manifest rows. ``pr_hygiene`` uses them for the
``charter:`` and ``archetype:`` checks. Nothing here touches the filesystem.
"""

from __future__ import annotations

import re

ARCH_DIR = "docs/architecture/"
STATUSES = ("chartered", "accepted for verification", "verified")
MANIFEST_NUMBER = 12

_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_STATUS_ROW = re.compile(r"^\| *Status *\|(.*?)\|[ \t]*$", re.MULTILINE)
_NUMBERED = re.compile(r"^## (\d+)\. +(.+?)[ \t]*$", re.MULTILINE)
_ANY_H2 = re.compile(r"^## ", re.MULTILINE)
_ROW_ID = re.compile(r"^\| *(M\d+) *\|", re.MULTILINE)


def is_slug(text: str) -> bool:
    return _SLUG.fullmatch(text) is not None


def doc_path(slug: str) -> str:
    return f"{ARCH_DIR}{slug}-protocol-design.md"


def status_value(body: str) -> str | None:
    """The Status cell with backticks, emphasis and spaces stripped, lower-cased."""
    match = _STATUS_ROW.search(body)
    if match is None:
        return None
    return match.group(1).strip().strip("`*").strip().lower()


def status_rank(value: str) -> int:
    return STATUSES.index(value)


def numbered_sections(body: str) -> list[tuple[int, str]]:
    return [(int(m.group(1)), m.group(2)) for m in _NUMBERED.finditer(body)]


def manifest_section(body: str) -> str | None:
    for match in _NUMBERED.finditer(body):
        if int(match.group(1)) == MANIFEST_NUMBER:
            rest = body[match.end() :]
            following = _ANY_H2.search(rest)
            return rest if following is None else rest[: following.start()]
    return None


def tier_staged_rows(body: str) -> list[str]:
    section = manifest_section(body)
    if section is None:
        return []
    return [
        m.group(1)
        for m in _ROW_ID.finditer(section)
        if "tier-staged" in section[m.start() : section.find("\n", m.start())]
    ]
