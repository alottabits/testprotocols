"""The ``[Unreleased]`` entries of CHANGELOG.md and their register rows.

``hygiene`` calls :func:`entry_problems` and :func:`register_problems` on a
PR that changes ``CHANGELOG.md`` or ``packages/testprotocols/DEPRECATIONS.md``
(CONTRIBUTING.md, "The changelog" and "The hygiene gate"). Only the
``[Unreleased]`` section is read; released sections are history.

Entry format (CONTRIBUTING.md, "The changelog"): a ``- **kind**`` bullet that
names the merged importable path in ``module:Symbol`` form, cites the proposal
path and item id (or says ``no proposal``) and then the PR number.

Register parity (DEPRECATIONS.md header, "Adding a row"): every row whose
"deprecated in" reads ``next release`` has a *Deprecated* entry under the same
package in ``[Unreleased]``, and every such entry has a row. A row and an entry
match when their kinds are equal and they name the same code spans in the same
order, read with the ``package.module:`` prefix dropped, ``\\|`` read as ``|``
and whitespace collapsed. A row with a released version belongs to that
release's section, which this check does not read.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

CHANGELOG = "CHANGELOG.md"
DEPRECATIONS = "packages/testprotocols/DEPRECATIONS.md"
PACKAGES = ("testprotocols", "testoperations")
PLACEHOLDERS = frozenset({"- no entries yet", "- no API change (version bump only)"})
NEXT_RELEASE = "next release"
# Entry kinds that describe no single public symbol (a cross-cutting behaviour, the
# deprecation marker, the type-checking setup): the format's symbol field does not apply.
NO_SYMBOL_KINDS = frozenset({"behaviour", "marker", "type checking"})
MODULE_KINDS = frozenset({"module", "modules"})

_PKG = "|".join(PACKAGES)
_KIND = re.compile(r"^- \*\*([^*]+)\*\*(?= )")
_IMPORTABLE = re.compile(rf"`(?:{_PKG})(?:\.[a-z_][a-z0-9_]*)*:[A-Za-z_]")
_MODULE_PATH = re.compile(rf"`(?:{_PKG})(?:\.[a-z_][a-z0-9_]*)+`")
_CITATION = re.compile(r"[Pp]roposal `docs/proposals/[^`]+\.md`,? P\d+|\bno proposal\b")
_PR_REF = re.compile(r"\bPRs? #\d+(?:(?:,\s*|\s+and\s+)#\d+)*")
_PR_NUMBER = re.compile(r"#(\d+)")
_SPAN = re.compile(r"`([^`]+)`")
_PREFIX = re.compile(rf"\b(?:{_PKG})(?:\.[a-z_][a-z0-9_]*)*:")
_CELL_SPLIT = re.compile(r"(?<!\\)\|")
_PACKAGE_LABEL = re.compile(rf"^\*\*({_PKG})\*\*\s*$")
_RULE_FORMAT = "(CONTRIBUTING.md, The changelog)"
_RULE_PARITY = "(DEPRECATIONS.md, Adding a row)"


@dataclass(frozen=True)
class Entry:
    """One ``[Unreleased]`` bullet with its continuation lines, joined by single spaces."""

    line: int  # 1-based line of the bullet in the file
    package: str
    subsection: str
    text: str

    @property
    def kind(self) -> str | None:
        match = _KIND.match(self.text)
        return None if match is None else match.group(1).strip()

    @property
    def subject(self) -> str:
        """What the entry names: the text after the kind, up to the first `` — ``."""
        body = _KIND.sub("", self.text, count=1).strip()
        return body.split(" — ", 1)[0]

    @property
    def key(self) -> tuple[str, str, str | None, str]:
        """Identity across an edit: package, subsection, kind and first code span."""
        first = _SPAN.search(self.subject)
        return (self.package, self.subsection, self.kind, "" if first is None else first.group(1))


@dataclass(frozen=True)
class Row:
    """One row of the deprecation register."""

    line: int
    package: str
    item: str
    kind: str
    deprecated_in: str


def _collapse(text: str) -> str:
    return " ".join(text.split())


def unreleased(text: str) -> tuple[list[Entry], int | None]:
    """The ``[Unreleased]`` entries of *text*, and the heading's line (``None``: no heading)."""
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith("## [Unreleased]")), None)
    if start is None:
        return [], None
    entries: list[Entry] = []
    package = subsection = ""
    current: list[str] = []
    first = 0

    def flush() -> None:
        if current:
            entries.append(Entry(first + 1, package, subsection, _collapse(" ".join(current))))
            current.clear()

    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line.startswith("## "):
            break
        if line.startswith("- "):
            flush()
            current.append(line)
            first = i
        elif current and line.startswith("  ") and line.strip():
            current.append(line)
        else:
            flush()
            if line.startswith("### "):
                package, subsection = line[4:].strip(), ""
            elif line.startswith("#### "):
                subsection = line[5:].strip()
    flush()
    return entries, start + 1


def cited_prs(text: str) -> set[int]:
    return {int(n) for ref in _PR_REF.finditer(text) for n in _PR_NUMBER.findall(ref.group(0))}


def format_problems(entry: Entry, path: str = CHANGELOG) -> list[str]:
    """One line per required field *entry* lacks."""
    if entry.text in PLACEHOLDERS:
        return []
    where = f"{path}:{entry.line}:"
    kind = entry.kind
    if kind is None:
        return [f"{where} entry does not start with a `**kind**` field {_RULE_FORMAT}"]
    problems: list[str] = []
    if kind in MODULE_KINDS:
        if _MODULE_PATH.search(entry.subject) is None and _IMPORTABLE.search(entry.subject) is None:
            problems.append(
                f"{where} `{kind}` entry names no importable module path "
                f"(`package.module`) {_RULE_FORMAT}"
            )
    elif kind not in NO_SYMBOL_KINDS and _IMPORTABLE.search(entry.subject) is None:
        problems.append(
            f"{where} `{kind}` entry names no symbol in merged importable `module:Symbol` form "
            f"before its ` — ` {_RULE_FORMAT}"
        )
    citation = _CITATION.search(entry.text)
    if citation is None:
        problems.append(
            f"{where} entry has no proposal path and item id (`Proposal "
            f"`docs/proposals/<file>.md` P<n>`) and does not say `no proposal` {_RULE_FORMAT}"
        )
    refs = list(_PR_REF.finditer(entry.text))
    if not refs:
        problems.append(f"{where} entry has no PR number (`PR #<n>`) {_RULE_FORMAT}")
    elif citation is not None and refs[-1].start() < citation.start():
        problems.append(
            f"{where} entry gives its PR number before the proposal citation; "
            f"the fields go in order {_RULE_FORMAT}"
        )
    return problems


def entry_problems(head: str, main: str, number: int, path: str = CHANGELOG) -> list[str]:
    """Format problems of every ``[Unreleased]`` entry in *head*, and the PR-number rule.

    An entry whose :attr:`Entry.key` is not among *main*'s ``[Unreleased]``
    entries is one this PR adds; it cites ``PR #<number>``. An edit to an
    existing entry keeps the PR number it had.
    """
    entries, heading = unreleased(head)
    if heading is None:
        return [f"{path}: no `## [Unreleased]` heading {_RULE_FORMAT}"]
    problems: list[str] = []
    for entry in entries:
        problems += format_problems(entry, path)
    on_main = Counter(e.key for e in unreleased(main)[0] if e.text not in PLACEHOLDERS)
    seen: Counter[tuple[str, str, str | None, str]] = Counter()
    for entry in entries:
        if entry.text in PLACEHOLDERS or entry.kind is None:
            continue
        seen[entry.key] += 1
        if seen[entry.key] <= on_main[entry.key] or number <= 0:
            continue
        if number not in cited_prs(entry.text):
            problems.append(
                f"{path}:{entry.line}: entry added by this PR cites "
                f"{', '.join(f'#{n}' for n in sorted(cited_prs(entry.text))) or 'no PR'}, "
                f"not this PR (`PR #{number}`) {_RULE_FORMAT}"
            )
    return problems


def register_rows(text: str) -> list[Row]:
    """The register's table rows, each under its ``**package**`` label."""
    rows: list[Row] = []
    package = ""
    for i, line in enumerate(text.splitlines()):
        label = _PACKAGE_LABEL.match(line)
        if label is not None:
            package = label.group(1)
            continue
        if not package or not line.startswith("|"):
            continue
        cells = [c.strip() for c in _CELL_SPLIT.split(line.strip())[1:-1]]
        if len(cells) != 5 or cells[0] == "item" or set(cells[0]) <= {"-", " ", ":"}:
            continue
        rows.append(Row(i + 1, package, cells[0], cells[2], cells[3]))
    return rows


def _spans(text: str) -> tuple[str, ...]:
    return tuple(
        _collapse(_PREFIX.sub("", span.replace("\\|", "|"))) for span in _SPAN.findall(text)
    )


def register_problems(
    changelog: str,
    register: str,
    changelog_path: str = CHANGELOG,
    register_path: str = DEPRECATIONS,
) -> list[str]:
    """Rows marked ``next release`` and ``[Unreleased]`` *Deprecated* entries, matched both ways."""
    rows = [r for r in register_rows(register) if r.deprecated_in == NEXT_RELEASE]
    entries = [
        e
        for e in unreleased(changelog)[0]
        if e.subsection == "Deprecated" and e.text not in PLACEHOLDERS
    ]
    unmatched = list(entries)
    problems: list[str] = []
    for row in rows:
        key = (row.package, row.kind, _spans(row.item))
        match = next((e for e in unmatched if (e.package, e.kind, _spans(e.subject)) == key), None)
        if match is None:
            problems.append(
                f"{register_path}:{row.line}: `{NEXT_RELEASE}` row ({row.kind}) has no "
                f"matching *Deprecated* entry under `### {row.package}` in {changelog_path} "
                f"[Unreleased] {_RULE_PARITY}"
            )
        else:
            unmatched.remove(match)
    problems += [
        f"{changelog_path}:{e.line}: *Deprecated* entry ({e.kind}) has no matching "
        f"`{NEXT_RELEASE}` row under **{e.package}** in {register_path} {_RULE_PARITY}"
        for e in unmatched
    ]
    return problems
