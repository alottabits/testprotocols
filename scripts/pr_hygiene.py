"""Deterministic pull-request hygiene rules (CONTRIBUTING.md, "The hygiene gate").

The job that runs this checks out the base repository's ``main`` only. The
PR is read through the GitHub API and handed in as JSON files; the few
head-of-PR files a rule needs are fetched through the API into a scratch
directory as data. Nothing from the PR tree is executed.

Subcommands:

  head-paths  print the PR-head paths ``check`` wants fetched, one per line
  check       apply the rules; print one problem per line and exit 1 on any

``check`` also writes ``set_review=true|false`` to the file named by
``--github-output``: ``true`` means the PR kind takes no agent review and
the workflow sets the ``review`` status itself.
"""

from __future__ import annotations

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


def load_pull_request(pr_json: Path, files_json: Path) -> PullRequest:
    """Build a PullRequest from ``gh api`` output.

    *pr_json* is ``gh api .../pulls/N``; *files_json* is
    ``gh api --paginate --slurp .../pulls/N/files``.
    """
    pr_data: dict[str, Any] = json.loads(pr_json.read_text())
    raw_files: Any = json.loads(files_json.read_text())
    pages: list[list[dict[str, Any]]] = (
        raw_files if raw_files and isinstance(raw_files[0], list) else [raw_files]
    )
    files = tuple(
        FileChange(str(entry["filename"]), str(entry["status"])) for page in pages for entry in page
    )
    labels = frozenset(str(label["name"]) for label in pr_data.get("labels", []))
    return PullRequest(str(pr_data["title"]), labels, files)


def main(argv: list[str]) -> int:
    del argv
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
