"""Tests for scripts/pr_hygiene.py."""

from __future__ import annotations

import pytest
from pr_hygiene import (
    FileChange,
    PullRequest,
    check_changelog,
    check_kind_scope,
    check_title,
    is_decision_file,
    is_source_path,
    parse_kind,
)

SRC = "packages/testprotocols/src/testprotocols/bgp.py"
OPS_SRC = "packages/testoperations/src/testoperations/homing.py"
TEST = "packages/testprotocols/tests/test_bgp.py"


def pr(
    title: str, *paths: str, labels: frozenset[str] = frozenset(), status: str = "modified"
) -> PullRequest:
    return PullRequest(title, labels, tuple(FileChange(p, status) for p in paths))


@pytest.mark.parametrize(
    ("title", "kind"),
    [
        ("proposal: overlay-advertisements", "proposal"),
        ("delta: overlay-advertisements", "delta"),
        ("feat: homing: flip one overlay subnet", "feat"),
        ("feat!: models: retype reserved_ranges", "feat"),
        ("fix: waiting: clamp the budget", "fix"),
        ("docs: fix a typo", "docs"),
        ("chore: bump ruff", "chore"),
        ("ci: pin actions", "ci"),
        ("test: cover both outcomes", "test"),
        ("release: 0.13.0", "release"),
        ("Feat: capitalised", None),
        ("feat(homing): scoped form is not recognised", None),
        ("feat:missing space", None),
        ("no prefix at all", None),
    ],
)
def test_parse_kind(title: str, kind: str | None) -> None:
    assert parse_kind(title) == kind


def test_path_classifiers() -> None:
    assert is_source_path(SRC) and is_source_path(OPS_SRC)
    assert not is_source_path(TEST)
    assert not is_source_path("packages/testprotocols/GAPS.md")
    assert is_decision_file("docs/architecture/bgp-protocol-design.md")
    assert is_decision_file("packages/testprotocols/GAPS.md")
    assert is_decision_file("packages/testprotocols/SPLITS.md")
    assert is_decision_file("packages/testprotocols/LEVELS.md")
    assert not is_decision_file("docs/proposals/2026-01-01-x.md")
    assert not is_decision_file("docs/architecture/notes/x.md")


def test_title_without_prefix_is_a_problem() -> None:
    assert check_title(pr("Add a thing", SRC)) == [
        "PR title has no recognised kind prefix (see CONTRIBUTING.md, PR kinds): 'Add a thing'"
    ]
    assert check_title(pr("feat: homing: a thing", SRC)) == []


def test_hygiene_only_kind_with_no_source_sets_review_status() -> None:
    assert check_kind_scope(pr("docs: typo", "README.md")) == ([], True)
    assert check_kind_scope(pr("test: more", TEST)) == ([], True)


def test_hygiene_only_kind_touching_source_is_mislabelled() -> None:
    problems, set_status = check_kind_scope(pr("chore: tidy", SRC, "README.md"))
    assert set_status is False
    assert problems == [
        "`chore:` PR changes package source; use `feat:` or `fix:` so it is reviewed: " + SRC
    ]


def test_hygiene_only_kind_touching_decision_file_waits_for_review() -> None:
    result = check_kind_scope(pr("docs: gaps entry", "packages/testprotocols/GAPS.md"))
    assert result == ([], False)


def test_reviewed_kinds_never_set_review_status() -> None:
    assert check_kind_scope(pr("feat: x: y", "README.md")) == ([], False)
    assert check_kind_scope(pr("release: 0.13.0", "CHANGELOG.md")) == ([], False)


def test_changelog_required_when_source_changes() -> None:
    assert check_changelog(pr("feat: x: y", SRC)) == [
        "package source changed but CHANGELOG.md has no [Unreleased] entry in this PR; "
        "add one or apply the `skip-changelog` label"
    ]
    assert check_changelog(pr("feat: x: y", SRC, "CHANGELOG.md")) == []
    assert check_changelog(pr("feat: x: y", SRC, labels=frozenset({"skip-changelog"}))) == []
    assert check_changelog(pr("docs: x", "README.md")) == []
