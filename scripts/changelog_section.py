"""One released version's section of CHANGELOG.md (CONTRIBUTING.md, "Releases").

``hygiene`` calls :func:`section` on a release PR's head, and ``release.yml``
runs this script at the tag to write the GitHub Release notes: the same
function decides both, so a section that would not publish cannot merge.

Usage: ``python scripts/changelog_section.py X.Y.Z [--file CHANGELOG.md]
[--check-versions] [--allow-empty]``. Prints the section to stdout, or each
reason to stderr with exit status 1. ``--check-versions`` also requires both
packages' ``[project] version`` to equal X.Y.Z. ``--allow-empty`` accepts a
version-bump-only section; it exists for the backfill's retroactive
Releases, and ``release.yml`` never passes it.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

NO_ENTRIES = "- no entries yet"
VERSION_BUMP_ONLY = "- no API change (version bump only)"
VERSION_FILES = (
    "packages/testprotocols/pyproject.toml",
    "packages/testoperations/pyproject.toml",
)

_VERSION = re.compile(r"^\d+\.\d+\.\d+$")
_NEXT_SECTION = re.compile(r"^## \[", re.MULTILINE)


class SectionError(Exception):
    """A released section that must not publish; the message is a one-line reason."""


def section(text: str, version: str, *, allow_empty: bool = False) -> str:
    """The body of ``## [version] — YYYY-MM-DD`` in *text*, stripped.

    Raises :class:`SectionError` when the heading is missing or repeated, when
    the section has no entry line, when it still carries ``- no entries yet``,
    and (unless *allow_empty*) when every entry is the version-bump-only line.
    """
    if not _VERSION.match(version):
        raise SectionError(f"version must be X.Y.Z: {version!r}")
    heading = re.compile(
        rf"^## \[{re.escape(version)}\] [—-] \d{{4}}-\d{{2}}-\d{{2}}.*$", re.MULTILINE
    )
    found = list(heading.finditer(text))
    if not found:
        raise SectionError(f"has no `## [{version}] — YYYY-MM-DD` heading")
    if len(found) > 1:
        raise SectionError(f"heading `## [{version}]` appears {len(found)} times")
    start = found[0].end()
    following = _NEXT_SECTION.search(text, start)
    body = text[start : following.start() if following else len(text)].strip()
    entries = [line.rstrip() for line in body.splitlines() if line.startswith("- ")]
    if not entries:
        raise SectionError("is empty")
    if NO_ENTRIES in entries:
        raise SectionError(f"still contains `{NO_ENTRIES}`")
    if not allow_empty and all(entry == VERSION_BUMP_ONLY for entry in entries):
        raise SectionError(f"has no entry beyond `{VERSION_BUMP_ONLY}`")
    return body


def version_problems(root: Path, version: str, *, source: str = "tag") -> list[str]:
    """One line per package whose ``[project] version`` under *root* is not *version*.

    *source* names where *version* came from, for the message: the tag here,
    the PR title in ``hygiene``.
    """
    problems: list[str] = []
    for rel in VERSION_FILES:
        try:
            found = tomllib.loads((root / rel).read_text(encoding="utf-8"))["project"]["version"]
        except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError):
            problems.append(f"{rel}: cannot read a [project] version")
            continue
        if found != version:
            problems.append(f"{rel}: version is {found}, {source} says {version}")
    return problems


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("version", help="X.Y.Z, without the tag's leading v")
    parser.add_argument("--file", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument("--check-versions", action="store_true")
    parser.add_argument("--allow-empty", action="store_true")
    args = parser.parse_args(argv)
    changelog: Path = args.file
    version: str = args.version
    allow_empty: bool = args.allow_empty
    check_versions: bool = args.check_versions
    try:
        text = changelog.read_text(encoding="utf-8")
    except OSError:
        print(f"{changelog}: cannot read the file", file=sys.stderr)
        return 1
    problems: list[str] = []
    body = ""
    try:
        body = section(text, version, allow_empty=allow_empty)
    except SectionError as exc:
        problems.append(f"{changelog}: released section {exc}")
    if check_versions:
        problems += version_problems(changelog.parent, version)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        return 1
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
