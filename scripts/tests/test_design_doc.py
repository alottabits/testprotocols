"""Tests for scripts/design_doc.py."""

from __future__ import annotations

import pytest
from design_doc import (
    STATUSES,
    doc_path,
    is_slug,
    manifest_section,
    numbered_sections,
    status_rank,
    status_value,
    tier_staged_rows,
)

DOC = """\
# Design: vendor-neutral **example** archetype

| Field | Value |
| --- | --- |
| Status | accepted for verification |
| Author | a maintainer |

## 1. Charter

Defined by published operations.

## 2. Cross-family matrix

...

## 12. Landing manifest

| Id | Kind | Symbol | Placement | Breaking | Outcome |
| --- | --- | --- | --- | --- | --- |
| M1 | new field | `m:X.enabled` | core | no | accepted |
| M2 | new tier | `m:Voice` | tier-staged — second consumer | no | accepted |
| M3 | GAPS entry | `m:Flows` | tier-staged — a test needs it | no | accepted |

## Review record

- 2026-09-30 — charter review: approve.
"""


@pytest.mark.parametrize(
    ("text", "ok"),
    [
        ("managed-router", True),
        ("wifi-ap", True),
        ("a1", True),
        ("Managed-Router", False),
        ("managed_router", False),
        ("managed router", False),
        ("-leading", False),
        ("trailing-", False),
        ("", False),
    ],
)
def test_is_slug(text: str, ok: bool) -> None:
    assert is_slug(text) is ok


def test_doc_path() -> None:
    assert doc_path("managed-router") == "docs/architecture/managed-router-protocol-design.md"


@pytest.mark.parametrize(
    ("cell", "value"),
    [
        ("chartered", "chartered"),
        ("`chartered`", "chartered"),
        ("**Chartered**", "chartered"),
        ("  verified  ", "verified"),
        ("Accepted for verification", "accepted for verification"),
        ("proposed — exploratory", "proposed — exploratory"),
    ],
)
def test_status_value_strips_decoration(cell: str, value: str) -> None:
    body = f"# T\n\n| Field | Value |\n| --- | --- |\n| Status | {cell} |\n"
    assert status_value(body) == value


def test_status_value_missing_row() -> None:
    assert status_value("# T\n\n| Field | Value |\n| --- | --- |\n| Author | x |\n") is None


def test_status_rank_orders_the_stages() -> None:
    assert [status_rank(s) for s in STATUSES] == [0, 1, 2]


def test_numbered_sections() -> None:
    assert numbered_sections(DOC) == [
        (1, "Charter"),
        (2, "Cross-family matrix"),
        (12, "Landing manifest"),
    ]
    assert numbered_sections("# T\n\n## Review record\n") == []


def test_manifest_section_and_tier_rows() -> None:
    section = manifest_section(DOC)
    assert section is not None
    assert "| M1 |" in section and "Review record" not in section
    assert tier_staged_rows(DOC) == ["M2", "M3"]
    assert manifest_section("# T\n\n## 1. Charter\n") is None
    assert tier_staged_rows("# T\n\n## 1. Charter\n") == []


def test_tier_rows_outside_the_manifest_are_ignored() -> None:
    body = "# T\n\n## 4. The archetype\n\n| M9 | tier-staged |\n\n## 12. Landing manifest\n\n"
    assert tier_staged_rows(body) == []
