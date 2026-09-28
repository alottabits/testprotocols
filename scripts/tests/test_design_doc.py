"""Tests for scripts/design_doc.py."""

from __future__ import annotations

import pytest
from design_doc import (
    STATUSES,
    doc_path,
    is_slug,
    manifest_problems,
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


def test_tier_rows_read_the_placement_cell_only() -> None:
    body = (
        "# T\n\n## 12. Landing manifest\n\n"
        "| Id | Kind | Symbol | Placement | Breaking | Outcome |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| M1 | new field | `m:X` | Tier-staged — second consumer | no | accepted |\n"
        "| M2 | new tier | `m:Y` | tier staged — a test needs it | no | accepted |\n"
        "| M3 | new field | `m:Z` | core | no | accepted; was tier-staged in round 1 |\n"
    )
    assert tier_staged_rows(body) == ["M1", "M2"]


LADDER_DOC = """\
# T

## 12. Landing manifest

| Id | Kind | Symbol | Mechanism | Placement | Breaking | Outcome |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | new field | `m:X.f` | defaulted field | core | no | accepted |
| M2 | new protocol | `m:Y` | new capability | core | no | accepted |
| M3 | rename | `m:Z` → `m:W`, deprecated alias | deprecate | core | no | accepted |
| M6 | new member | `m:Y.more` | extend | core | yes | accepted |
| M7 | removal | `m:Z` after its deprecation | remove | core | yes | accepted |
| M4 | SPLITS entry | the rename | record | core | no | accepted |
| M5 | new tier | `m:Tier` | archetype | tier-staged — x | no | accepted |
"""


def test_a_ladder_manifest_is_clean() -> None:
    assert manifest_problems(LADDER_DOC) == []


def test_manifest_needs_a_mechanism_column() -> None:
    body = LADDER_DOC.replace(" Mechanism |", " Notes |")
    assert manifest_problems(body) == [
        "the landing manifest has no Mechanism column (docs/archetypes/README.md, "
        "The placement ladder)"
    ]


def test_mechanism_values_and_breaking_agreement() -> None:
    body = LADDER_DOC.replace("| defaulted field | core | no |", "| field-ish | core | no |")
    body = body.replace("| extend | core | yes |", "| extend | core | no |")
    body = body.replace("| new capability | core | no |", "| New Capability | core | yes |")
    assert manifest_problems(body) == [
        "M1: Mechanism 'field-ish' is not a placement-ladder rung (driver-only, reuse, "
        "defaulted field, white-box, extend, deprecate, remove, new capability, "
        "archetype, record)",
        "M2: Breaking is 'yes' but Mechanism 'new capability' is not breaking",
        "M6: Mechanism 'extend' needs Breaking 'yes'",
    ]


def test_no_manifest_no_problems() -> None:
    assert manifest_problems("# T\n\n## 1. Charter\n") == []


def test_escaped_pipes_stay_inside_their_cell() -> None:
    body = LADDER_DOC.replace(
        "| M1 | new field | `m:X.f` | defaulted field |",
        "| M1 | new field | `m:X.f` (`int \\| None = None`) | defaulted field |",
    )
    assert manifest_problems(body) == []
    tier = body.replace("| archetype | tier-staged — x |", "| archetype | tier-staged — a \\| b |")
    assert tier_staged_rows(tier) == ["M5"]
