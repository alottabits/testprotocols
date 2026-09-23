"""The `/review` gate (CONTRIBUTING.md, "A PR's life", step 3).

Pure decisions over data the workflow fetched through the API: who commented
and with what access, whether they are a maintainer, whether the PR is a
draft, and whether the deterministic checks are green on the head commit.
Prints `ok` and exits 0 when the review may start, otherwise the reason and
exit 1. The workflow posts the reason as a PR comment.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REQUIRED_CHECKS = ("dco", "lint", "hygiene")
WRITE_PERMISSIONS = frozenset({"admin", "maintain", "write"})
_LIST_HEADING = re.compile(r"^## Maintainers\s*$", re.MULTILINE)
_ENTRY = re.compile(r"^- @([A-Za-z0-9-]+)(?:\s|$)", re.MULTILINE)


def maintainers(text: str) -> frozenset[str]:
    """Handles listed under the `## Maintainers` heading, lower-cased."""
    heading = _LIST_HEADING.search(text)
    if heading is None:
        return frozenset()
    section = text[heading.end() :]
    next_heading = re.search(r"^#{1,6} ", section, re.MULTILINE)
    if next_heading is not None:
        section = section[: next_heading.start()]
    return frozenset(m.group(1).lower() for m in _ENTRY.finditer(section))


def refusal(
    *,
    body: str,
    commenter: str,
    permission: str,
    maintainers_text: str,
    is_draft: bool,
    checks: dict[str, str],
) -> str | None:
    """Why the review may not start, or ``None``."""
    if body.strip() != "/review":
        return "the comment must be exactly `/review`"
    if permission not in WRITE_PERMISSIONS:
        return f"@{commenter} does not have write access"
    if commenter.lower() not in maintainers(maintainers_text):
        return f"@{commenter} is not listed in MAINTAINERS.md"
    if is_draft:
        return "the PR is a draft"
    for name in REQUIRED_CHECKS:
        conclusion = checks.get(name, "missing")
        if conclusion != "success":
            return f"{name} is {conclusion} on the head commit"
    return None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--body", required=True, type=Path)
    parser.add_argument("--commenter", required=True)
    parser.add_argument("--permission", required=True)
    parser.add_argument("--maintainers", required=True, type=Path)
    parser.add_argument("--pr", required=True, type=Path, help="gh api repos/O/R/pulls/N output")
    parser.add_argument("--checks", required=True, type=Path, help='{"dco": "success", ...}')
    args = parser.parse_args(argv)
    body_path: Path = args.body
    maintainers_path: Path = args.maintainers
    pr_path: Path = args.pr
    checks_path: Path = args.checks
    pr_data: dict[str, Any] = json.loads(pr_path.read_text(encoding="utf-8"))
    checks_data: dict[str, str] = json.loads(checks_path.read_text(encoding="utf-8"))
    reason = refusal(
        body=body_path.read_text(encoding="utf-8"),
        commenter=str(args.commenter),
        permission=str(args.permission),
        maintainers_text=maintainers_path.read_text(encoding="utf-8"),
        is_draft=bool(pr_data.get("draft", False)),
        checks=checks_data,
    )
    print(reason if reason is not None else "ok")
    return 0 if reason is None else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
