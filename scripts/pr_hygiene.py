"""Deterministic pull-request hygiene rules (CONTRIBUTING.md, "The hygiene gate").

The job that runs this checks out the base repository's ``main`` only. The
PR is read through the GitHub API and handed in as JSON files; the few
head-of-PR files a rule needs are fetched through the API into a scratch
directory as data. Nothing from the PR tree is executed.

Subcommands:

  head-paths  print the PR-head paths ``check`` wants fetched, one per line
  reviewers   print the reviewer set a PR takes, comma-joined
  check       apply the rules; print one problem per line and exit 1 on any

``check`` also writes ``set_review=true|false`` to the file named by
``--github-output``: ``true`` means the PR kind takes no agent review and
the workflow sets the ``review`` status itself.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

KINDS = ("proposal", "delta", "feat", "fix", "docs", "chore", "ci", "test", "release")
HYGIENE_ONLY_KINDS = frozenset({"docs", "chore", "ci", "test"})
SOURCE_GLOB = "packages/*/src/*"
DECISION_FILE_GLOBS = (
    "docs/architecture/*.md",
    "packages/testprotocols/GAPS.md",
    "packages/testprotocols/SPLITS.md",
    "packages/testprotocols/LEVELS.md",
)
CHANGELOG = "CHANGELOG.md"
SKIP_CHANGELOG_LABEL = "skip-changelog"

_TITLE = re.compile(r"^(proposal|delta|feat!?|fix|docs|chore|ci|test|release): \S")


@dataclass(frozen=True)
class FileChange:
    path: str
    status: str  # added | modified | removed | renamed


@dataclass(frozen=True)
class PullRequest:
    title: str
    labels: frozenset[str]
    files: tuple[FileChange, ...]

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(f.path for f in self.files)


def parse_kind(title: str) -> str | None:
    """The PR kind named by *title*'s prefix, or ``None`` when it has none."""
    match = _TITLE.match(title)
    return None if match is None else match.group(1).rstrip("!")


def is_source_path(path: str) -> bool:
    return fnmatch.fnmatchcase(path, SOURCE_GLOB)


def is_decision_file(path: str) -> bool:
    # fnmatch's `*` crosses `/`; the architecture glob must stay one level deep.
    return any(fnmatch.fnmatchcase(path, glob) for glob in DECISION_FILE_GLOBS) and not (
        path.startswith("docs/architecture/") and path.count("/") > 2
    )


def check_title(pr: PullRequest) -> list[str]:
    if parse_kind(pr.title) is None:
        return [
            f"PR title has no recognised kind prefix (see CONTRIBUTING.md, PR kinds): {pr.title!r}"
        ]
    return []


def check_kind_scope(pr: PullRequest) -> tuple[list[str], bool]:
    """Problems for a mislabelled hygiene-only PR, and whether to set the review status."""
    kind = parse_kind(pr.title)
    if kind not in HYGIENE_ONLY_KINDS:
        return [], False
    source = [p for p in pr.paths if is_source_path(p)]
    if source:
        return (
            [
                f"`{kind}:` PR changes package source; use `feat:` or `fix:` so it is reviewed: "
                + ", ".join(source)
            ],
            False,
        )
    if any(is_decision_file(p) for p in pr.paths):
        return [], False  # a decision file takes the proposal reviewer: wait for /review
    return [], True


def check_changelog(pr: PullRequest) -> list[str]:
    if SKIP_CHANGELOG_LABEL in pr.labels:
        return []
    if any(is_source_path(p) for p in pr.paths) and CHANGELOG not in pr.paths:
        return [
            "package source changed but CHANGELOG.md has no [Unreleased] entry in this PR; "
            f"add one or apply the `{SKIP_CHANGELOG_LABEL}` label"
        ]
    return []


PROPOSAL_DIR = "docs/proposals/"
VERSION_FILES = (
    "packages/testprotocols/pyproject.toml",
    "packages/testoperations/pyproject.toml",
)
GAPS = "packages/testprotocols/GAPS.md"
HEADER_ROWS = ("Date", "Use case", "Round", "Status")

_PROPOSAL_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
_RELEASE_TITLE = re.compile(r"^release: (\d+\.\d+\.\d+)$")
_VERSION_FIELD = re.compile(r'^version = "([^"]+)"', re.MULTILINE)
_P1_BLOCK = re.compile(r"^### P1\b", re.MULTILINE)
_OUTCOME_SECTION = re.compile(
    r"^#+ [^\n]*Outcome[^\n]*\n(.*?)(?=^#+ |\Z)", re.MULTILINE | re.DOTALL
)
_LOCAL_OR_DECLINED = re.compile(r"keep[ -]local|declin", re.IGNORECASE)


@dataclass(frozen=True)
class Result:
    problems: list[str]
    set_review_status: bool


def _is_proposal_doc(path: str) -> bool:
    return path.startswith(PROPOSAL_DIR) and path != PROPOSAL_DIR + "README.md"


def _safe_relative(path: str) -> bool:
    parts = path.split("/")
    return bool(path) and not path.startswith("/") and ".." not in parts


def _read_head(head_root: Path, rel: str) -> str | None:
    target = head_root / rel
    return target.read_text(encoding="utf-8") if target.is_file() else None


def check_proposal_dir(pr: PullRequest) -> list[str]:
    """Documents under docs/proposals/ enter through a proposal: PR and change under review.

    A non-``proposal:`` kind may not add one. A hygiene-only kind may not modify
    one either, since nothing reviews it. A ``feat:``, ``fix:`` or ``release:`` PR
    may modify an existing one: that is the in-PR design delta of the process,
    and the PR is reviewed.
    """
    kind = parse_kind(pr.title)
    if kind in {"proposal", "delta"}:
        return []
    added = [f.path for f in pr.files if f.status == "added" and _is_proposal_doc(f.path)]
    problems: list[str] = []
    if added:
        problems.append(
            "a new document under docs/proposals/ enters through a `proposal:` PR: "
            + ", ".join(added)
        )
    if kind in HYGIENE_ONLY_KINDS:
        modified = [f.path for f in pr.files if f.status != "added" and _is_proposal_doc(f.path)]
        if modified:
            problems.append(
                f"a `{kind}:` PR may not change a document under docs/proposals/; "
                "use `delta:` or land the change with the `feat:` that needs it: "
                + ", ".join(modified)
            )
    return problems


def check_proposal(pr: PullRequest, head_root: Path) -> list[str]:
    if parse_kind(pr.title) != "proposal":
        return []
    rule = "a proposal: PR adds exactly one file under docs/proposals/ and touches nothing else; "
    added = [f.path for f in pr.files if f.status == "added" and _is_proposal_doc(f.path)]
    others = [p for p in pr.paths if p not in added]
    if len(added) != 1:
        return [rule + ("no added proposal file" if not added else "several: " + ", ".join(added))]
    if others:
        return [rule + "also changed: " + ", ".join(others)]
    path = added[0]
    if not _PROPOSAL_NAME.match(path.removeprefix(PROPOSAL_DIR)):
        return [f"proposal file name must match YYYY-MM-DD-<slug>.md: {path}"]
    body = _read_head(head_root, path)
    if body is None:
        return [f"{path}: could not read the file from the PR head"]
    problems: list[str] = []
    missing = [row for row in HEADER_ROWS if not re.search(rf"^\| *{row} *\|", body, re.MULTILINE)]
    if missing:
        problems.append(f"{path}: header table is missing rows: " + ", ".join(missing))
    if _P1_BLOCK.search(body) is None:
        problems.append(f"{path}: no `### P1` block")
    return problems


def check_delta(pr: PullRequest) -> list[str]:
    if parse_kind(pr.title) != "delta":
        return []
    ok = (
        len(pr.files) == 1
        and pr.files[0].status == "modified"
        and _is_proposal_doc(pr.files[0].path)
    )
    if ok:
        return []
    return ["a delta: PR modifies exactly one existing file under docs/proposals/ and nothing else"]


def check_release(pr: PullRequest, head_root: Path) -> list[str]:
    if parse_kind(pr.title) != "release":
        return []
    match = _RELEASE_TITLE.match(pr.title)
    if match is None:
        return [f"release: title must be `release: X.Y.Z`: {pr.title!r}"]
    version = match.group(1)
    problems: list[str] = []
    for rel in VERSION_FILES:
        body = _read_head(head_root, rel)
        found = None if body is None else _VERSION_FIELD.search(body)
        if found is None:
            problems.append(f"{rel}: could not read a version field from the PR head")
        elif found.group(1) != version:
            problems.append(f"{rel}: version is {found.group(1)}, title says {version}")
    changelog = _read_head(head_root, CHANGELOG)
    if changelog is None:
        problems.append(f"{CHANGELOG}: could not read the file from the PR head")
        return problems
    heading = re.search(
        rf"^## \[{re.escape(version)}\] [—-] \d{{4}}-\d{{2}}-\d{{2}}", changelog, re.MULTILINE
    )
    if heading is None:
        problems.append(f"{CHANGELOG}: no `## [{version}] — YYYY-MM-DD` heading")
        return problems
    unreleased = changelog.find("## [Unreleased]")
    if unreleased < 0 or unreleased > heading.start():
        problems.append(
            f"{CHANGELOG}: no fresh `## [Unreleased]` heading above the release heading"
        )
    return problems


def check_gaps_pointers(pr: PullRequest, main_root: Path) -> list[str]:
    if parse_kind(pr.title) not in {"proposal", "release"}:
        return []
    gaps_path = main_root / GAPS
    gaps = gaps_path.read_text(encoding="utf-8") if gaps_path.is_file() else ""
    problems: list[str] = []
    proposals_dir = main_root / PROPOSAL_DIR
    if not proposals_dir.is_dir():
        return []
    for doc in sorted(proposals_dir.glob("*.md")):
        rel = PROPOSAL_DIR + doc.name
        if not _is_proposal_doc(rel):
            continue
        flagged = any(
            _LOCAL_OR_DECLINED.search(m.group(1))
            for m in _OUTCOME_SECTION.finditer(doc.read_text(encoding="utf-8"))
        )
        if not flagged:
            continue
        if rel not in gaps:
            problems.append(
                f"{GAPS} has no pointer to {rel} (its Outcome has a keep-local or declined item)"
            )
    return problems


REVIEWED_KINDS = {
    "proposal": "proposal",
    "delta": "proposal",
    "feat": "code",
    "fix": "code",
    "release": "release",
}
REVIEWER_ORDER = ("code", "release", "proposal")


def reviewers_for(pr: PullRequest) -> list[str]:
    """The reviewer set a PR takes: by kind, plus the proposal reviewer for a decision file."""
    kind = parse_kind(pr.title)
    if kind is None:
        return []
    chosen: set[str] = {REVIEWED_KINDS[kind]} if kind in REVIEWED_KINDS else set()
    if any(is_decision_file(p) for p in pr.paths):
        chosen.add("proposal")
    return [r for r in REVIEWER_ORDER if r in chosen]


def head_paths(pr: PullRequest) -> list[str]:
    """PR-head files the checks read; the workflow fetches them through the API."""
    kind = parse_kind(pr.title)
    if kind == "proposal":
        return [
            f.path
            for f in pr.files
            if f.status == "added" and _is_proposal_doc(f.path) and _safe_relative(f.path)
        ]
    if kind == "release":
        return [*VERSION_FILES, CHANGELOG]
    return []


def run_checks(pr: PullRequest, main_root: Path, head_root: Path) -> Result:
    problems = check_title(pr)
    scope_problems, set_review = check_kind_scope(pr)
    problems += scope_problems
    problems += check_changelog(pr)
    problems += check_proposal_dir(pr)
    problems += check_proposal(pr, head_root)
    problems += check_delta(pr)
    problems += check_release(pr, head_root)
    problems += check_gaps_pointers(pr, main_root)
    return Result(problems, set_review and not problems)


def load_pull_request(pr_json: Path, files_json: Path) -> PullRequest:
    """Build a PullRequest from ``gh api`` output.

    *pr_json* is ``gh api .../pulls/N``; *files_json* is
    ``gh api --paginate .../pulls/N/files | jq -s add``.
    """
    pr_data: dict[str, Any] = json.loads(pr_json.read_text(encoding="utf-8"))
    # `jq -s 'add'` over zero pages prints `null`; read that as no files.
    raw_files: Any = json.loads(files_json.read_text(encoding="utf-8")) or []
    pages: list[list[dict[str, Any]]] = (
        raw_files if raw_files and isinstance(raw_files[0], list) else [raw_files]
    )
    files = tuple(
        FileChange(str(entry["filename"]), str(entry["status"])) for page in pages for entry in page
    )
    labels = frozenset(str(label["name"]) for label in pr_data.get("labels", []))
    return PullRequest(str(pr_data["title"]), labels, files)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("head-paths", "reviewers", "check"):
        p = sub.add_parser(name)
        p.add_argument("--pr", required=True, type=Path, help="gh api repos/O/R/pulls/N output")
        p.add_argument(
            "--files",
            required=True,
            type=Path,
            help="gh api --paginate .../pulls/N/files | jq -s add output",
        )
        if name == "check":
            p.add_argument("--main-root", required=True, type=Path)
            p.add_argument("--head-root", required=True, type=Path)
            p.add_argument("--github-output", type=Path, default=None)
    args = parser.parse_args(argv)
    pr_path: Path = args.pr
    files_path: Path = args.files
    pr = load_pull_request(pr_path, files_path)
    if args.command == "head-paths":
        for path in head_paths(pr):
            print(path)
        return 0
    if args.command == "reviewers":
        print(",".join(reviewers_for(pr)))
        return 0
    main_root: Path = args.main_root
    head_root: Path = args.head_root
    github_output: Path | None = args.github_output
    result = run_checks(pr, main_root, head_root)
    if github_output is not None:
        with github_output.open("a") as out:
            out.write(f"set_review={'true' if result.set_review_status else 'false'}\n")
    for problem in result.problems:
        print(f"hygiene: {problem}")
    if result.problems:
        print(f"\n{len(result.problems)} hygiene problem(s). See CONTRIBUTING.md.")
        return 1
    print("hygiene: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
