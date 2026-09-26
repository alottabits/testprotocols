"""Tests for scripts/pr_hygiene.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pr_hygiene import (
    FileChange,
    PullRequest,
    Result,
    check_archetype,
    check_changelog,
    check_charter,
    check_delta,
    check_gaps_pointers,
    check_kind_scope,
    check_maintainer_opened,
    check_proposal,
    check_proposal_dir,
    check_release,
    check_title,
    head_paths,
    is_decision_file,
    is_source_path,
    load_pull_request,
    main,
    parse_kind,
    reviewers_for,
    run_checks,
    title_slug,
)

SRC = "packages/testprotocols/src/testprotocols/bgp.py"
OPS_SRC = "packages/testoperations/src/testoperations/homing.py"
TEST = "packages/testprotocols/tests/test_bgp.py"
DESIGN = "docs/architecture/managed-router-protocol-design.md"


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
        ("charter: managed-router", "charter"),
        ("archetype: managed-router", "archetype"),
        ("archetype!: managed-router", None),
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


ADDED_MESSAGE = (
    "a new document under docs/proposals/ enters through a `proposal:` PR: "
    "docs/proposals/2026-01-01-y.md"
)


def modify_message(kind: str) -> str:
    return (
        f"a `{kind}:` PR may not change a document under docs/proposals/; "
        "use `delta:` or land the change with the `feat:` that needs it: "
        "docs/proposals/2026-01-01-y.md"
    )


def test_proposal_docs_need_proposal_or_delta_kind() -> None:
    new_doc = "docs/proposals/2026-01-01-y.md"
    # A new document enters only through a `proposal:` PR, whatever the kind.
    assert check_proposal_dir(pr("docs: x", new_doc, status="added")) == [ADDED_MESSAGE]
    assert check_proposal_dir(pr("feat: x: y", SRC, new_doc, status="added")) == [ADDED_MESSAGE]
    # A reviewed kind may carry the in-PR design delta on an existing document.
    assert check_proposal_dir(pr("feat: x: y", SRC, new_doc)) == []
    assert check_proposal_dir(pr("fix: x: y", SRC, new_doc)) == []
    assert check_proposal_dir(pr("release: 0.13.0", new_doc)) == []
    # A hygiene-only kind may not: nothing reviews it.
    assert check_proposal_dir(pr("docs: x", new_doc)) == [modify_message("docs")]
    assert check_proposal_dir(pr("chore: x", new_doc)) == [modify_message("chore")]
    assert check_proposal_dir(pr("docs: readme", "docs/proposals/README.md")) == []
    assert check_proposal_dir(pr("proposal: x", PROPOSAL, status="added")) == []
    assert check_proposal_dir(pr("delta: x", PROPOSAL)) == []


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
    good = (
        "# Changelog\n\n## [Unreleased]\n\n## [0.13.0] — 2026-09-21\n\n### testprotocols\n\n"
        "- **operation** `testoperations.homing:set_subnet_advertised` — "
        "flip. No proposal; PR #1.\n"
    )
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


def test_release_reads_the_project_version_only(tmp_path: Path) -> None:
    # A `version =` key outside [project] must not be taken for the package version.
    changelog = (
        "# Changelog\n\n## [Unreleased]\n\n## [0.13.0] — 2026-09-21\n\n### testprotocols\n\n"
        "- **model** `testprotocols.models:X` — x. No proposal; PR #1.\n"
    )
    release_head(tmp_path, "0.13.0", "0.13.0", changelog)
    write(
        tmp_path,
        "packages/testprotocols/pyproject.toml",
        '[tool.other]\nversion = "9.9.9"\n\n'
        '[project]\nname = "testprotocols"\nversion = "0.13.0"\n',
    )
    assert check_release(pr("release: 0.13.0", "CHANGELOG.md"), tmp_path) == []
    write(
        tmp_path, "packages/testoperations/pyproject.toml", '[project]\nname = "testoperations"\n'
    )
    assert check_release(pr("release: 0.13.0", "CHANGELOG.md"), tmp_path) == [
        "packages/testoperations/pyproject.toml: cannot read a [project] version"
    ]


@pytest.mark.parametrize(
    ("released", "reason"),
    [
        ("### testprotocols\n\n#### Added\n", "is empty"),
        ("### testprotocols\n\n- no entries yet\n", "still contains `- no entries yet`"),
        (
            "### testprotocols\n\n- no API change (version bump only)\n\n"
            "### testoperations\n\n- no API change (version bump only)\n",
            "has no entry beyond `- no API change (version bump only)`",
        ),
    ],
)
def test_release_section_must_publish(tmp_path: Path, released: str, reason: str) -> None:
    changelog = f"# Changelog\n\n## [Unreleased]\n\n## [0.13.0] — 2026-09-21\n\n{released}"
    release_head(tmp_path, "0.13.0", "0.13.0", changelog)
    assert check_release(pr("release: 0.13.0", "CHANGELOG.md"), tmp_path) == [
        f"CHANGELOG.md: released section {reason}"
    ]


def test_release_section_duplicate_heading(tmp_path: Path) -> None:
    entry = "### testprotocols\n\n- **model** `testprotocols.models:X` — x. No proposal; PR #1.\n\n"
    changelog = (
        "# Changelog\n\n## [Unreleased]\n\n"
        f"## [0.13.0] — 2026-09-21\n\n{entry}## [0.13.0] — 2026-09-21\n\n{entry}"
    )
    release_head(tmp_path, "0.13.0", "0.13.0", changelog)
    assert check_release(pr("release: 0.13.0", "CHANGELOG.md"), tmp_path) == [
        "CHANGELOG.md: released section heading `## [0.13.0]` appears 2 times"
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


def test_gaps_pointer_reads_every_outcome_section(tmp_path: Path) -> None:
    write(tmp_path, "docs/proposals/README.md", "# Proposals\n")
    write(
        tmp_path,
        "docs/proposals/2026-08-01-thing.md",
        "# Thing\n\n"
        "## Outcome (round 1)\n\n- P1: accepted\n\n"
        "## Outcome (round 2)\n\n- P1: declined\n",
    )
    write(tmp_path, "packages/testprotocols/GAPS.md", "# Log\n")
    assert check_gaps_pointers(pr("release: 0.13.0", "CHANGELOG.md"), tmp_path) == [
        "packages/testprotocols/GAPS.md has no pointer to docs/proposals/2026-08-01-thing.md "
        "(its Outcome has a keep-local or declined item)"
    ]
    write(
        tmp_path,
        "packages/testprotocols/GAPS.md",
        "# Log\n\nSee docs/proposals/2026-08-01-thing.md.\n",
    )
    assert check_gaps_pointers(pr("release: 0.13.0", "CHANGELOG.md"), tmp_path) == []


def test_gaps_pointer_ignores_subsections_after_outcome(tmp_path: Path) -> None:
    write(tmp_path, "docs/proposals/README.md", "# Proposals\n")
    write(
        tmp_path,
        "docs/proposals/2026-08-01-thing.md",
        "# Thing\n\n"
        "### Outcome\n\n- P1: accepted\n\n"
        "### Next steps\n\nthe declined alternative is out of scope\n",
    )
    write(tmp_path, "packages/testprotocols/GAPS.md", "# Log\n")
    assert check_gaps_pointers(pr("release: 0.13.0", "CHANGELOG.md"), tmp_path) == []


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


def test_run_checks_flags_proposal_dir_touched_by_wrong_kind(tmp_path: Path) -> None:
    main_root = tmp_path / "main"
    head_root = tmp_path / "head"
    gaps_main(main_root, "- P1: accepted", "# Log\n")
    result = run_checks(
        pr("docs: x", "docs/proposals/2026-01-01-y.md", status="added"), main_root, head_root
    )
    assert len(result.problems) == 1
    assert result.set_review_status is False


def test_load_pull_request_tolerates_an_empty_file_list(tmp_path: Path) -> None:
    # `jq -s 'add'` over zero pages prints `null`, not `[]`.
    pr_json = tmp_path / "pr.json"
    files_json = tmp_path / "files.json"
    pr_json.write_text(json.dumps({"title": "docs: typo", "labels": []}))
    files_json.write_text("null\n")
    assert load_pull_request(pr_json, files_json) == PullRequest("docs: typo", frozenset(), ())


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


@pytest.mark.parametrize(
    ("title", "paths", "expected"),
    [
        ("proposal: x", (PROPOSAL,), ["proposal"]),
        ("delta: x", (PROPOSAL,), ["proposal"]),
        ("feat: x: y", (SRC,), ["code"]),
        ("feat!: x: y", (SRC,), ["code"]),
        ("fix: x: y", (SRC,), ["code"]),
        ("release: 0.13.0", ("CHANGELOG.md",), ["release"]),
        ("feat: x: y", (SRC, "packages/testprotocols/SPLITS.md"), ["code", "proposal"]),
        ("docs: x", ("docs/architecture/bgp-protocol-design.md",), ["proposal"]),
        ("docs: x", ("README.md",), []),
        ("chore: x", ("packages/testprotocols/GAPS.md",), ["proposal"]),
        ("no prefix", (SRC,), []),
        ("charter: managed-router", (DESIGN,), ["archetype"]),
        ("archetype: managed-router", (DESIGN,), ["archetype"]),
        ("archetype: managed-router", (DESIGN, SRC, "CHANGELOG.md"), ["code", "archetype"]),
        (
            "archetype: managed-router",
            (DESIGN, SRC, "packages/testprotocols/SPLITS.md"),
            ["code", "archetype"],
        ),
    ],
)
def test_reviewers_for(title: str, paths: tuple[str, ...], expected: list[str]) -> None:
    assert reviewers_for(pr(title, *paths)) == expected


def test_reviewers_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pr_json = tmp_path / "pr.json"
    files_json = tmp_path / "files.json"
    pr_json.write_text(json.dumps({"title": "feat: x: y", "labels": []}))
    files_json.write_text(
        json.dumps(
            [
                {"filename": SRC, "status": "modified"},
                {"filename": "packages/testprotocols/LEVELS.md", "status": "modified"},
            ]
        )
    )
    assert main(["reviewers", "--pr", str(pr_json), "--files", str(files_json)]) == 0
    assert capsys.readouterr().out == "code,proposal\n"
    pr_json.write_text(json.dumps({"title": "docs: x", "labels": []}))
    files_json.write_text(json.dumps([{"filename": "README.md", "status": "modified"}]))
    assert main(["reviewers", "--pr", str(pr_json), "--files", str(files_json)]) == 0
    assert capsys.readouterr().out == "\n"


def test_load_pull_request_reads_the_author(tmp_path: Path) -> None:
    pr_json = tmp_path / "pr.json"
    files_json = tmp_path / "files.json"
    pr_json.write_text(
        json.dumps({"title": "charter: x", "labels": [], "user": {"login": "RJVisser"}})
    )
    files_json.write_text("[]")
    assert load_pull_request(pr_json, files_json).author == "RJVisser"
    pr_json.write_text(json.dumps({"title": "charter: x", "labels": []}))
    assert load_pull_request(pr_json, files_json).author == ""


MAINTAINERS = """\
# Maintainers

~~~text
- @handle — <scope>
~~~

## Maintainers

- @rjvisser — everything (`*`)
"""

CHARTER_DOC = """\
# Design: vendor-neutral **managed router** archetype

| Field | Value |
| --- | --- |
| Status | chartered |
| Author | a maintainer |

## 1. Charter

The class, defined by the operations its management planes publish.

## Review record

- none yet
"""


def charter_pr(*files: FileChange, title: str = "charter: managed-router") -> PullRequest:
    return PullRequest(title, frozenset(), files, author="rjvisser")


def test_title_slug() -> None:
    assert title_slug(pr("charter: managed-router", DESIGN)) == "managed-router"
    assert title_slug(pr("archetype: wifi-ap", DESIGN)) == "wifi-ap"
    assert title_slug(pr("charter: Managed Router", DESIGN)) is None
    assert title_slug(pr("archetype: managed_router", DESIGN)) is None
    assert title_slug(pr("feat: x: y", SRC)) is None


def test_archetype_kinds_are_maintainer_opened(tmp_path: Path) -> None:
    write(tmp_path, "MAINTAINERS.md", MAINTAINERS)
    ok = PullRequest("charter: managed-router", frozenset(), (), author="RJVisser")
    assert check_maintainer_opened(ok, tmp_path) == []
    outsider = PullRequest("archetype: managed-router", frozenset(), (), author="someone")
    assert check_maintainer_opened(outsider, tmp_path) == [
        "a `archetype:` PR is opened by a maintainer listed in MAINTAINERS.md; "
        "@someone is not listed (a consumer requests an archetype with the "
        "archetype-request issue template)"
    ]
    handle = PullRequest("charter: x", frozenset(), (), author="handle")
    assert check_maintainer_opened(handle, tmp_path) != []  # the fenced example is not a listing
    assert check_maintainer_opened(pr("feat: x: y", SRC), tmp_path) == []


def test_charter_adds_exactly_its_design_document(tmp_path: Path) -> None:
    write(tmp_path, DESIGN, CHARTER_DOC)
    assert check_charter(charter_pr(FileChange(DESIGN, "added")), tmp_path) == []
    rule = f"a charter: PR adds exactly {DESIGN} and touches nothing else; changed: "
    assert check_charter(charter_pr(FileChange(DESIGN, "modified")), tmp_path) == [
        rule + f"{DESIGN} (modified)"
    ]
    assert check_charter(
        charter_pr(FileChange(DESIGN, "added"), FileChange("README.md", "modified")), tmp_path
    ) == [rule + f"{DESIGN} (added), README.md (modified)"]
    other = "docs/architecture/router-protocol-design.md"
    assert check_charter(charter_pr(FileChange(other, "added")), tmp_path) == [
        rule + f"{other} (added)"
    ]
    assert check_charter(charter_pr(), tmp_path) == [rule + "nothing"]


def test_charter_title_needs_a_slug(tmp_path: Path) -> None:
    assert check_charter(
        charter_pr(FileChange(DESIGN, "added"), title="charter: Managed Router"), tmp_path
    ) == [
        "charter: title must be `charter: <slug>`, lowercase words joined by hyphens: "
        "'charter: Managed Router'"
    ]
    assert head_paths(charter_pr(FileChange(DESIGN, "added"), title="charter: ../x")) == []


def test_charter_document_is_chartered_and_holds_only_the_charter(tmp_path: Path) -> None:
    write(tmp_path, DESIGN, CHARTER_DOC.replace("| chartered |", "| `Chartered` |"))
    assert check_charter(charter_pr(FileChange(DESIGN, "added")), tmp_path) == []
    write(tmp_path, DESIGN, CHARTER_DOC.replace("| chartered |", "| verified |"))
    assert check_charter(charter_pr(FileChange(DESIGN, "added")), tmp_path) == [
        f"{DESIGN}: Status is 'verified'; a charter enters as `chartered`"
    ]
    write(tmp_path, DESIGN, CHARTER_DOC.replace("| Status | chartered |\n", ""))
    assert check_charter(charter_pr(FileChange(DESIGN, "added")), tmp_path) == [
        f"{DESIGN}: header table has no Status row"
    ]
    write(tmp_path, DESIGN, CHARTER_DOC + "\n## 2. Cross-family matrix\n")
    assert check_charter(charter_pr(FileChange(DESIGN, "added")), tmp_path) == [
        f"{DESIGN}: a charter holds only `## 1. Charter` (and an unnumbered "
        "`## Review record`); found: 1. Charter, 2. Cross-family matrix"
    ]
    write(tmp_path, DESIGN, CHARTER_DOC.replace("## 1. Charter", "## Charter"))
    assert check_charter(charter_pr(FileChange(DESIGN, "added")), tmp_path) == [
        f"{DESIGN}: a charter holds only `## 1. Charter` (and an unnumbered "
        "`## Review record`); found: no numbered section"
    ]


def test_charter_document_missing_from_head(tmp_path: Path) -> None:
    assert check_charter(charter_pr(FileChange(DESIGN, "added")), tmp_path) == [
        f"{DESIGN}: could not read the file from the PR head"
    ]


def test_charter_head_paths() -> None:
    assert head_paths(charter_pr(FileChange(DESIGN, "added"))) == [DESIGN]


def design_doc(status: str, *, manifest: str = "") -> str:
    body = CHARTER_DOC.replace("| chartered |", f"| {status} |")
    body = body.replace("## Review record", "## 2. Cross-family matrix\n\n...\n\n## Review record")
    if manifest:
        body = body.replace(
            "## Review record",
            "## 12. Landing manifest\n\n| Id | Kind | Symbol | Placement | Breaking | Outcome |\n"
            f"| --- | --- | --- | --- | --- | --- |\n{manifest}\n## Review record",
        )
    return body


CORE_ROW = "| M1 | new field | `m:X.enabled` | core | no | accepted |\n"
TIER_ROW = "| M2 | new tier | `m:V` | tier-staged — 2nd consumer | no | accepted |\n"


def archetype_pr(*files: FileChange) -> PullRequest:
    return PullRequest("archetype: managed-router", frozenset(), files, author="rjvisser")


def roots(tmp_path: Path, main_doc: str | None, head_doc: str | None) -> tuple[Path, Path]:
    main_root, head_root = tmp_path / "main", tmp_path / "head"
    main_root.mkdir(parents=True)
    head_root.mkdir(parents=True)
    if main_doc is not None:
        write(main_root, DESIGN, main_doc)
    if head_doc is not None:
        write(head_root, DESIGN, head_doc)
    return main_root, head_root


def test_archetype_design_stage_is_clean(tmp_path: Path) -> None:
    main_root, head_root = roots(tmp_path, CHARTER_DOC, design_doc("chartered"))
    assert check_archetype(archetype_pr(FileChange(DESIGN, "modified")), main_root, head_root) == []
    main_root2, head_root2 = roots(
        tmp_path / "b", CHARTER_DOC, design_doc("accepted for verification")
    )
    assert (
        check_archetype(archetype_pr(FileChange(DESIGN, "modified")), main_root2, head_root2) == []
    )


def test_archetype_needs_its_chartered_document_on_main(tmp_path: Path) -> None:
    main_root, head_root = roots(tmp_path, None, design_doc("chartered"))
    assert check_archetype(archetype_pr(FileChange(DESIGN, "added")), main_root, head_root) == [
        f"an archetype: PR modifies {DESIGN}, which a merged charter added",
        f"{DESIGN} is not on main; merge its `charter:` PR first",
    ]


def test_archetype_rejects_a_renamed_or_second_design_document(tmp_path: Path) -> None:
    main_root, head_root = roots(tmp_path, CHARTER_DOC, design_doc("chartered"))
    other = "docs/architecture/bgp-protocol-design.md"
    assert check_archetype(
        archetype_pr(FileChange(DESIGN, "modified"), FileChange(other, "modified")),
        main_root,
        head_root,
    ) == [
        "an archetype: PR changes only its design document, package source and tests, "
        f"CHANGELOG.md and the tracking files; also changed: {other}"
    ]
    assert check_archetype(archetype_pr(FileChange(DESIGN, "renamed")), main_root, head_root) == [
        f"an archetype: PR modifies {DESIGN}, which a merged charter added"
    ]


def test_archetype_allows_code_tests_changelog_and_tracking_files(tmp_path: Path) -> None:
    head = design_doc("accepted for verification", manifest=CORE_ROW)
    main_root, head_root = roots(tmp_path, CHARTER_DOC, head)
    files = (
        FileChange(DESIGN, "modified"),
        FileChange(SRC, "modified"),
        FileChange(TEST, "added"),
        FileChange("CHANGELOG.md", "modified"),
        FileChange("packages/testprotocols/SPLITS.md", "modified"),
        FileChange("packages/testprotocols/LEVELS.md", "modified"),
        FileChange("packages/testprotocols/GAPS.md", "modified"),
    )
    assert check_archetype(archetype_pr(*files), main_root, head_root) == []


def test_archetype_status_values_and_direction(tmp_path: Path) -> None:
    main_root, head_root = roots(tmp_path, CHARTER_DOC, design_doc("proposed"))
    assert check_archetype(archetype_pr(FileChange(DESIGN, "modified")), main_root, head_root) == [
        f"{DESIGN}: Status must be one of chartered, accepted for verification, verified; "
        "found 'proposed'"
    ]
    main_root2, head_root2 = roots(
        tmp_path / "b", design_doc("accepted for verification"), design_doc("chartered")
    )
    assert check_archetype(
        archetype_pr(FileChange(DESIGN, "modified")), main_root2, head_root2
    ) == [f"{DESIGN}: Status moves backwards: accepted for verification on main, chartered here"]


def test_archetype_source_needs_acceptance_and_a_manifest(tmp_path: Path) -> None:
    main_root, head_root = roots(tmp_path, CHARTER_DOC, design_doc("chartered"))
    files = (FileChange(DESIGN, "modified"), FileChange(SRC, "modified"))
    assert check_archetype(archetype_pr(*files), main_root, head_root) == [
        f"{DESIGN}: package source arrives at stage 4; the design review sets Status to "
        "`accepted for verification` first",
        f"{DESIGN}: package source is present but there is no `## 12. Landing manifest` section",
    ]


def test_archetype_verified_needs_gaps_pointers_for_tier_rows(tmp_path: Path) -> None:
    head = design_doc("verified", manifest=CORE_ROW + TIER_ROW)
    main_root, head_root = roots(tmp_path, design_doc("accepted for verification"), head)
    files = (FileChange(DESIGN, "modified"), FileChange(SRC, "modified"))
    assert check_archetype(archetype_pr(*files), main_root, head_root) == [
        "packages/testprotocols/GAPS.md: could not read the file from the PR head"
    ]
    write(head_root, "packages/testprotocols/GAPS.md", "# Log\n")
    assert check_archetype(archetype_pr(*files), main_root, head_root) == [
        f"packages/testprotocols/GAPS.md has no pointer to {DESIGN} (tier-staged rows: M2)"
    ]
    write(head_root, "packages/testprotocols/GAPS.md", f"# Log\n\nSee {DESIGN} M2.\n")
    assert check_archetype(archetype_pr(*files), main_root, head_root) == []


def test_archetype_head_document_missing(tmp_path: Path) -> None:
    main_root, head_root = roots(tmp_path, CHARTER_DOC, None)
    assert check_archetype(archetype_pr(FileChange(DESIGN, "modified")), main_root, head_root) == [
        f"{DESIGN}: could not read the file from the PR head"
    ]


def test_archetype_title_and_head_paths(tmp_path: Path) -> None:
    bad = PullRequest("archetype: managed_router", frozenset(), (FileChange(DESIGN, "modified"),))
    assert check_archetype(bad, tmp_path, tmp_path) == [
        "archetype: title must be `archetype: <slug>`, lowercase words joined by hyphens: "
        "'archetype: managed_router'"
    ]
    assert head_paths(bad) == []
    assert head_paths(archetype_pr(FileChange(DESIGN, "modified"))) == [
        DESIGN,
        "packages/testprotocols/GAPS.md",
    ]
