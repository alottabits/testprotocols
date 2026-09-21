"""Tests for scripts/pr_hygiene.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pr_hygiene import (
    FileChange,
    PullRequest,
    Result,
    check_changelog,
    check_delta,
    check_gaps_pointers,
    check_kind_scope,
    check_proposal,
    check_release,
    check_title,
    head_paths,
    is_decision_file,
    is_source_path,
    main,
    parse_kind,
    run_checks,
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


PROPOSAL = "docs/proposals/2026-09-21-overlay-advertisements.md"
GOOD_PROPOSAL = """\
# Overlay advertisements

| Field | Value |
| --- | --- |
| Date | 2026-09-21 |
| Use case | UC-019 — observe what a site advertises into the overlay |
| Round | 1 |
| Status | under review |

### P1 — capability protocol `OverlayAdvertisements`

Need ...
"""


def write(root: Path, rel: str, text: str) -> None:
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


def test_proposal_must_add_exactly_one_well_named_file(tmp_path: Path) -> None:
    write(tmp_path, PROPOSAL, GOOD_PROPOSAL)
    assert (
        check_proposal(pr("proposal: overlay-advertisements", PROPOSAL, status="added"), tmp_path)
        == []
    )
    assert check_proposal(
        pr("proposal: x", "docs/proposals/bad name.md", status="added"), tmp_path
    ) == ["proposal file name must match YYYY-MM-DD-<slug>.md: docs/proposals/bad name.md"]
    assert check_proposal(pr("proposal: x", PROPOSAL, "README.md", status="added"), tmp_path) == [
        "a proposal: PR adds exactly one file under docs/proposals/ and touches nothing else; "
        "also changed: README.md"
    ]
    assert check_proposal(pr("proposal: x", PROPOSAL, status="modified"), tmp_path) == [
        "a proposal: PR adds exactly one file under docs/proposals/ and touches nothing else; "
        "no added proposal file"
    ]


def test_proposal_body_needs_header_table_and_p1(tmp_path: Path) -> None:
    write(tmp_path, PROPOSAL, "# Title\n\n### P1 — thing\n")
    assert check_proposal(pr("proposal: x", PROPOSAL, status="added"), tmp_path) == [
        f"{PROPOSAL}: header table is missing rows: Date, Use case, Round, Status"
    ]
    write(tmp_path, PROPOSAL, GOOD_PROPOSAL.replace("### P1", "### Item 1"))
    assert check_proposal(pr("proposal: x", PROPOSAL, status="added"), tmp_path) == [
        f"{PROPOSAL}: no `### P1` block"
    ]


def test_proposal_file_missing_from_head_is_reported(tmp_path: Path) -> None:
    assert check_proposal(pr("proposal: x", PROPOSAL, status="added"), tmp_path) == [
        f"{PROPOSAL}: could not read the file from the PR head"
    ]


def test_delta_modifies_one_merged_proposal_only() -> None:
    assert check_delta(pr("delta: overlay-advertisements", PROPOSAL)) == []
    assert check_delta(pr("delta: x", PROPOSAL, "README.md")) == [
        "a delta: PR modifies exactly one existing file under docs/proposals/ and nothing else"
    ]
    assert check_delta(pr("delta: x", PROPOSAL, status="added")) == [
        "a delta: PR modifies exactly one existing file under docs/proposals/ and nothing else"
    ]


def release_head(root: Path, tp: str, to: str, changelog: str) -> None:
    write(
        root,
        "packages/testprotocols/pyproject.toml",
        f'[project]\nname = "testprotocols"\nversion = "{tp}"\n',
    )
    write(
        root,
        "packages/testoperations/pyproject.toml",
        f'[project]\nname = "testoperations"\nversion = "{to}"\n',
    )
    write(root, "CHANGELOG.md", changelog)


def test_release_versions_and_heading(tmp_path: Path) -> None:
    good = "# Changelog\n\n## [Unreleased]\n\n## [0.13.0] — 2026-09-21\n\n### testprotocols\n"
    release_head(tmp_path, "0.13.0", "0.13.0", good)
    assert check_release(pr("release: 0.13.0", "CHANGELOG.md"), tmp_path) == []

    release_head(tmp_path, "0.13.0", "0.12.1", good)
    assert check_release(pr("release: 0.13.0", "CHANGELOG.md"), tmp_path) == [
        "packages/testoperations/pyproject.toml: version is 0.12.1, title says 0.13.0"
    ]

    release_head(
        tmp_path,
        "0.13.0",
        "0.13.0",
        "# Changelog\n\n## [Unreleased]\n\n## [0.12.1] — 2026-09-10\n",
    )
    assert check_release(pr("release: 0.13.0", "CHANGELOG.md"), tmp_path) == [
        "CHANGELOG.md: no `## [0.13.0] — YYYY-MM-DD` heading"
    ]

    release_head(tmp_path, "0.13.0", "0.13.0", "# Changelog\n\n## [0.13.0] — 2026-09-21\n")
    assert check_release(pr("release: 0.13.0", "CHANGELOG.md"), tmp_path) == [
        "CHANGELOG.md: no fresh `## [Unreleased]` heading above the release heading"
    ]


def test_release_title_must_be_a_version() -> None:
    assert check_release(pr("release: next", "CHANGELOG.md"), Path("/nonexistent")) == [
        "release: title must be `release: X.Y.Z`: 'release: next'"
    ]


def gaps_main(root: Path, outcome: str, gaps: str) -> None:
    write(root, "docs/proposals/README.md", "# Proposals\n")
    write(
        root,
        "docs/proposals/2026-08-01-thing.md",
        f"# Thing\n\n### P1\n\n## Outcome\n\n{outcome}\n",
    )
    write(root, "packages/testprotocols/GAPS.md", gaps)


def test_gaps_pointer_required_for_keep_local_and_declined(tmp_path: Path) -> None:
    gaps_main(tmp_path, "- P1: keep local, 2026-08-02", "# Missing-capability log\n")
    assert check_gaps_pointers(pr("release: 0.13.0", "CHANGELOG.md"), tmp_path) == [
        "packages/testprotocols/GAPS.md has no pointer to docs/proposals/2026-08-01-thing.md "
        "(its Outcome has a keep-local or declined item)"
    ]
    gaps_main(
        tmp_path,
        "- P1: declined, 2026-08-02",
        "# Log\n\n## 2026-08-02 — thing\n\nSee docs/proposals/2026-08-01-thing.md.\n",
    )
    assert check_gaps_pointers(pr("proposal: x", PROPOSAL), tmp_path) == []
    gaps_main(tmp_path, "- P1: accepted, 2026-08-02", "# Log\n")
    assert check_gaps_pointers(pr("proposal: x", PROPOSAL), tmp_path) == []


def test_gaps_pointer_check_only_on_proposal_and_release(tmp_path: Path) -> None:
    gaps_main(tmp_path, "- P1: keep local", "# Log\n")
    assert check_gaps_pointers(pr("feat: x: y", SRC), tmp_path) == []


def test_head_paths() -> None:
    assert head_paths(pr("proposal: x", PROPOSAL, status="added")) == [PROPOSAL]
    assert head_paths(pr("release: 0.13.0", "CHANGELOG.md")) == [
        "packages/testprotocols/pyproject.toml",
        "packages/testoperations/pyproject.toml",
        "CHANGELOG.md",
    ]
    assert head_paths(pr("feat: x: y", SRC)) == []
    assert head_paths(pr("proposal: x", "docs/proposals/../../etc/passwd", status="added")) == []


def test_run_checks_collects_everything(tmp_path: Path) -> None:
    main_root = tmp_path / "main"
    head_root = tmp_path / "head"
    gaps_main(main_root, "- P1: accepted", "# Log\n")
    result = run_checks(pr("docs: typo", "README.md"), main_root, head_root)
    assert result == Result([], True)
    result = run_checks(pr("bad title", SRC), main_root, head_root)
    assert result.set_review_status is False
    assert len(result.problems) == 2
    assert result.problems[0].startswith("PR title has no recognised kind prefix")
    assert result.problems[1].startswith("package source changed but CHANGELOG.md")


def test_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pr_json = tmp_path / "pr.json"
    files_json = tmp_path / "files.json"
    pr_json.write_text(json.dumps({"title": "docs: typo", "labels": []}))
    files_json.write_text(json.dumps([[{"filename": "README.md", "status": "modified"}]]))
    output = tmp_path / "out.txt"
    main_root = tmp_path / "main"
    gaps_main(main_root, "- P1: accepted", "# Log\n")
    assert main(["head-paths", "--pr", str(pr_json), "--files", str(files_json)]) == 0
    assert capsys.readouterr().out == ""
    code = main(
        [
            "check",
            "--pr",
            str(pr_json),
            "--files",
            str(files_json),
            "--main-root",
            str(main_root),
            "--head-root",
            str(tmp_path / "head"),
            "--github-output",
            str(output),
        ]
    )
    assert code == 0
    assert output.read_text() == "set_review=true\n"

    pr_json.write_text(json.dumps({"title": "feat: x: y", "labels": []}))
    files_json.write_text(json.dumps([[{"filename": SRC, "status": "modified"}]]))
    code = main(
        [
            "check",
            "--pr",
            str(pr_json),
            "--files",
            str(files_json),
            "--main-root",
            str(main_root),
            "--head-root",
            str(tmp_path / "head"),
            "--github-output",
            str(output),
        ]
    )
    assert code == 1
    assert "CHANGELOG.md" in capsys.readouterr().out
    assert output.read_text().endswith("set_review=false\n")
