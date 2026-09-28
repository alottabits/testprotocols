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
_CELL_SEP = re.compile(r"(?<!\\)\|")


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


def _cells(line: str) -> list[str]:
    """A table row's cells; an escaped pipe (``\\|``) stays inside its cell."""
    return [c.strip() for c in _CELL_SEP.split(line.strip().strip("|"))]


def manifest_section(body: str) -> str | None:
    for match in _NUMBERED.finditer(body):
        if int(match.group(1)) == MANIFEST_NUMBER:
            rest = body[match.end() :]
            following = _ANY_H2.search(rest)
            return rest if following is None else rest[: following.start()]
    return None


def tier_staged_rows(body: str) -> list[str]:
    """Ids of manifest rows whose Placement cell is tier-staged.

    The Placement column is found by its header; without one, the fourth
    column is read (the manifest layout before the Mechanism column).
    """
    section = manifest_section(body)
    if section is None:
        return []
    placement_at = 3
    rows: list[str] = []
    for line in section.splitlines():
        cells = _cells(line)
        if line.strip().startswith("|") and "placement" in [c.lower() for c in cells]:
            placement_at = [c.lower() for c in cells].index("placement")
            continue
        match = _ROW_ID.match(line)
        if match is None:
            continue
        placement = (
            cells[placement_at].lower().replace(" ", "-") if len(cells) > placement_at else ""
        )
        if placement.startswith("tier-staged"):
            rows.append(match.group(1))
    return rows


MECHANISMS = (
    "driver-only",
    "reuse",
    "defaulted field",
    "white-box",
    "extend",
    "deprecate",
    "remove",
    "new capability",
    "archetype",
    "record",
)
#: Rungs that break existing implementers or callers in the release that lands them.
BREAKING_MECHANISMS = frozenset({"extend", "remove"})


def manifest_problems(body: str) -> list[str]:
    """Placement-ladder checks on the landing manifest (docs/archetypes/README.md).

    Every row names its Mechanism, one of ``MECHANISMS``; the Breaking column
    says yes exactly for the rungs in ``BREAKING_MECHANISMS``.
    """
    section = manifest_section(body)
    if section is None:
        return []
    lines = [line.strip() for line in section.splitlines() if line.strip().startswith("|")]
    if not lines:
        return []
    header = [c.lower() for c in _cells(lines[0])]
    if "mechanism" not in header:
        return [
            "the landing manifest has no Mechanism column (docs/archetypes/README.md, "
            "The placement ladder)"
        ]
    mech_at = header.index("mechanism")
    breaking_at = header.index("breaking") if "breaking" in header else None
    problems: list[str] = []
    for line in lines[1:]:
        cells = _cells(line)
        if not cells or _ROW_ID.match(line) is None or len(cells) <= mech_at:
            continue
        row, mechanism = cells[0], cells[mech_at].lower()
        if mechanism not in MECHANISMS:
            problems.append(
                f"{row}: Mechanism {cells[mech_at]!r} is not a placement-ladder rung "
                f"({', '.join(MECHANISMS)})"
            )
            continue
        if breaking_at is None or len(cells) <= breaking_at:
            continue
        breaking = cells[breaking_at].lower().startswith("yes")
        if mechanism in BREAKING_MECHANISMS and not breaking:
            problems.append(f"{row}: Mechanism {mechanism!r} needs Breaking 'yes'")
        elif mechanism not in BREAKING_MECHANISMS and breaking:
            problems.append(f"{row}: Breaking is 'yes' but Mechanism {mechanism!r} is not breaking")
    return problems
