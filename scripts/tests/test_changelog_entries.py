"""Tests for scripts/changelog_entries.py and its hygiene rule."""

from __future__ import annotations

from pathlib import Path

from changelog_entries import (
    entry_problems,
    format_problems,
    register_problems,
    register_rows,
    unreleased,
)
from pr_hygiene import FileChange, PullRequest, check_changelog_entries, run_checks

FIXTURES = Path(__file__).parent / "fixtures" / "main"
PROPOSAL = "Proposal `docs/proposals/2026-08-23-overlay-advertisements.md` P1"
GOOD = (
    "- **capability protocol** `testprotocols.overlay:OverlayAdvertisements` —\n"
    "  read the overlay subnets a site advertises, keyed by subnet.\n"
    f"  {PROPOSAL}; PR #31.\n"
)
DEPRECATED = (
    "- **member** `testprotocols.router:Router.get_telemetry` — deprecated. Replacement:\n"
    "  `read_telemetry`. Earliest removal: the first release 6 months after the release.\n"
    f"  {PROPOSAL}; PR #31.\n"
)
ROW = (
    "| `testprotocols.router:Router.get_telemetry` | `read_telemetry` | member "
    "| next release | next release + 6 months |"
)
REGISTER_HEAD = (
    "# Deprecation register\n\n**testprotocols**\n\n"
    "| item | replacement | kind | deprecated in | earliest removal |\n"
    "| --- | --- | --- | --- | --- |\n"
)


def changelog(
    added: str = GOOD, deprecated: str = "", ops: str = "- no entries yet\n", released: str = ""
) -> str:
    text = "# Changelog\n\n## [Unreleased]\n\n### testprotocols\n\n#### Added\n\n" + added
    if deprecated:
        text += "\n#### Deprecated\n\n" + deprecated
    text += "\n### testoperations\n\n" + ops
    return text + "\n## [0.12.1] — 2026-09-09\n\n### testprotocols\n\n" + (released or GOOD)


def problems_of(entry: str) -> list[str]:
    entries, _ = unreleased(changelog(added=entry))
    return format_problems(entries[0])


def test_a_good_entry_passes() -> None:
    assert problems_of(GOOD) == []
    assert problems_of(GOOD.replace(PROPOSAL, "no proposal: a maintainer addition")) == []
    assert problems_of(GOOD.replace("PR #31", "PRs #31 and #32")) == []


def test_entries_are_read_with_line_package_and_subsection() -> None:
    entries, heading = unreleased(changelog(deprecated=DEPRECATED))
    assert heading == 3
    assert [(e.line, e.package, e.subsection) for e in entries] == [
        (9, "testprotocols", "Added"),
        (15, "testprotocols", "Deprecated"),
        (21, "testoperations", ""),
    ]
    assert entries[0].kind == "capability protocol"
    assert entries[0].subject == "`testprotocols.overlay:OverlayAdvertisements`"


def test_placeholder_lines_are_not_entries_to_check() -> None:
    entries, _ = unreleased(changelog())
    assert format_problems(entries[-1]) == []


def test_missing_kind() -> None:
    [problem] = problems_of(GOOD.replace("**capability protocol** ", ""))
    assert problem.startswith("CHANGELOG.md:9: entry does not start with a `**kind**` field")


def test_bare_symbol_is_a_problem() -> None:
    [problem] = problems_of(GOOD.replace("testprotocols.overlay:", ""))
    assert problem.startswith(
        "CHANGELOG.md:9: `capability protocol` entry names no symbol in merged importable "
        "`module:Symbol` form"
    )
    assert problem.endswith("(CONTRIBUTING.md, The changelog)")
    # A module path alone is not a symbol, and a path only in the behaviour line does not count.
    assert problems_of(GOOD.replace(":OverlayAdvertisements", ""))
    moved = "- **protocol** `Overlay` — see `testprotocols.overlay:Overlay`.\n  " + PROPOSAL
    assert problems_of(moved + "; PR #31.\n")


def test_symbol_rule_by_kind() -> None:
    module = (
        "- **module** `testoperations.pairs` — the pair readers.\n  " + PROPOSAL + "; PR #31.\n"
    )
    assert problems_of(module) == []
    assert problems_of(module.replace("testoperations.pairs", "pairs"))
    behaviour = "- **behaviour** the operations convert words.\n  " + PROPOSAL + "; PR #31.\n"
    assert problems_of(behaviour) == []


def test_missing_citation() -> None:
    [problem] = problems_of(GOOD.replace(PROPOSAL + "; ", ""))
    assert "no proposal path and item id" in problem and problem.startswith("CHANGELOG.md:9:")
    # A path without the item id is not a citation.
    assert problems_of(GOOD.replace(" P1;", ";"))


def test_missing_pr_number() -> None:
    [problem] = problems_of(GOOD.replace("; PR #31", ""))
    assert problem == "CHANGELOG.md:9: entry has no PR number (`PR #<n>`) " + (
        "(CONTRIBUTING.md, The changelog)"
    )
    # CONTRIBUTING names the PR number; `PR pending` is not one.
    assert problems_of(GOOD.replace("PR #31", "PR pending"))


def test_pr_number_after_the_citation() -> None:
    swapped = GOOD.replace(f"{PROPOSAL}; PR #31.", f"PR #31; {PROPOSAL}.")
    [problem] = problems_of(swapped)
    assert "gives its PR number before the proposal citation" in problem


def test_added_entry_cites_this_pr() -> None:
    main = changelog()
    head = changelog(added=GOOD + GOOD.replace("OverlayAdvertisements", "OverlayRoutes"))
    [problem] = entry_problems(head, main, 40)
    assert problem.startswith("CHANGELOG.md:12: entry added by this PR cites #31, not this PR")
    assert "`PR #40`" in problem
    cited = changelog(added=GOOD.replace("#31", "#40") + GOOD.replace("#31", "#40"))
    assert entry_problems(cited, main, 40) == []


def test_edited_entry_keeps_its_pr_number() -> None:
    main = changelog()
    head = changelog(added=GOOD.replace("keyed by subnet", "keyed by prefix"))
    assert entry_problems(head, main, 40) == []
    # A second entry with the same key is an added one.
    assert len(entry_problems(changelog(added=GOOD + GOOD), main, 40)) == 1
    # The same entry moved to another subsection is an added one.
    moved = changelog(added="- no entries yet\n", deprecated=GOOD)
    assert len(entry_problems(moved, main, 40)) == 1


def test_released_sections_are_not_read() -> None:
    old = "- **thing** `Bare` — released before the format.\n"
    assert entry_problems(changelog(released=old), changelog(released=old), 40) == []


def test_unreleased_heading_required() -> None:
    assert entry_problems("# Changelog\n", "", 40) == [
        "CHANGELOG.md: no `## [Unreleased]` heading (CONTRIBUTING.md, The changelog)"
    ]


def test_register_rows_are_parsed() -> None:
    register = REGISTER_HEAD + ROW + "\n| `A.b(x)`: `E \\| str` | `E` | parameter | 0.12.0 | x |\n"
    rows = register_rows(register)
    assert [(r.line, r.package, r.kind, r.deprecated_in) for r in rows] == [
        (7, "testprotocols", "member", "next release"),
        (8, "testprotocols", "parameter", "0.12.0"),
    ]
    assert rows[1].item == "`A.b(x)`: `E \\| str`"


def test_register_parity_match() -> None:
    assert register_problems(changelog(deprecated=DEPRECATED), REGISTER_HEAD + ROW + "\n") == []
    # The register may leave out the module prefix; `\\|` in a cell reads as `|`.
    short = ROW.replace("testprotocols.router:", "")
    assert register_problems(changelog(deprecated=DEPRECATED), REGISTER_HEAD + short + "\n") == []
    union = DEPRECATED.replace(
        "`testprotocols.router:Router.get_telemetry` —",
        "`testprotocols.nat:Nat.list_nat_rules(mode)`: `NatMode | str` —",
    )
    row = ROW.replace(
        "`testprotocols.router:Router.get_telemetry`",
        "`Nat.list_nat_rules(mode)`: `NatMode \\| str`",
    )
    assert register_problems(changelog(deprecated=union), REGISTER_HEAD + row + "\n") == []


def test_register_row_without_entry() -> None:
    [problem] = register_problems(changelog(), REGISTER_HEAD + ROW + "\n")
    assert problem == (
        "packages/testprotocols/DEPRECATIONS.md:7: `next release` row (member) has no matching "
        "*Deprecated* entry under `### testprotocols` in CHANGELOG.md [Unreleased] "
        "(DEPRECATIONS.md, Adding a row)"
    )


def test_deprecated_entry_without_row() -> None:
    [problem] = register_problems(changelog(deprecated=DEPRECATED), REGISTER_HEAD)
    assert problem == (
        "CHANGELOG.md:15: *Deprecated* entry (member) has no matching `next release` row under "
        "**testprotocols** in packages/testprotocols/DEPRECATIONS.md "
        "(DEPRECATIONS.md, Adding a row)"
    )


def test_register_parity_mismatch_both_ways() -> None:
    other = ROW.replace("get_telemetry", "get_status")
    problems = register_problems(changelog(deprecated=DEPRECATED), REGISTER_HEAD + other + "\n")
    assert [p.split(":")[0] for p in problems] == [
        "packages/testprotocols/DEPRECATIONS.md",
        "CHANGELOG.md",
    ]
    # Same symbol, different kind: no match.
    assert (
        len(
            register_problems(
                changelog(deprecated=DEPRECATED),
                REGISTER_HEAD + ROW.replace("| member |", "| class |") + "\n",
            )
        )
        == 2
    )
    # Same symbol, other package: no match.
    ops = REGISTER_HEAD.replace("**testprotocols**", "**testoperations**") + ROW + "\n"
    assert len(register_problems(changelog(deprecated=DEPRECATED), ops)) == 2


def test_released_rows_are_not_matched_against_unreleased() -> None:
    released = ROW.replace("| next release | next release + 6 months |", "| 0.12.0 | 0.14.0 |")
    assert register_problems(changelog(), REGISTER_HEAD + released + "\n") == []


def test_main_files_pass() -> None:
    text = (FIXTURES / "CHANGELOG.md").read_text(encoding="utf-8")
    register = (FIXTURES / "DEPRECATIONS.md").read_text(encoding="utf-8")
    assert len(unreleased(text)[0]) > 100
    assert len([r for r in register_rows(register) if r.deprecated_in == "next release"]) > 50
    assert entry_problems(text, text, 76) == []
    assert register_problems(text, register) == []


def write(root: Path, rel: str, text: str) -> None:
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def pull(title: str, *paths: str, number: int = 40) -> PullRequest:
    return PullRequest(
        title, frozenset(), tuple(FileChange(p, "modified") for p in paths), "", number
    )


def test_hygiene_rule_applies_when_either_file_changes(tmp_path: Path) -> None:
    main_root, head_root = tmp_path / "main", tmp_path / "head"
    write(main_root, "CHANGELOG.md", changelog())
    write(head_root, "CHANGELOG.md", changelog(added=GOOD + GOOD.replace("Advertisements", "X")))
    write(head_root, "packages/testprotocols/DEPRECATIONS.md", REGISTER_HEAD + ROW + "\n")
    assert check_changelog_entries(pull("docs: x", "README.md"), main_root, head_root) == []
    problems = check_changelog_entries(pull("fix: x: y", "CHANGELOG.md"), main_root, head_root)
    assert [p.split(":")[1] for p in problems] == ["12", "7"]
    only_register = pull("fix: x: y", "packages/testprotocols/DEPRECATIONS.md")
    assert len(check_changelog_entries(only_register, main_root, head_root)) == 2
    result = run_checks(pull("fix: x: y", "CHANGELOG.md"), main_root, head_root)
    assert len(result.problems) == 2


def test_hygiene_rule_reports_an_unreadable_head_file(tmp_path: Path) -> None:
    write(tmp_path / "head", "CHANGELOG.md", changelog())
    problems = check_changelog_entries(
        pull("fix: x: y", "CHANGELOG.md"), tmp_path, tmp_path / "head"
    )
    assert problems == [
        "packages/testprotocols/DEPRECATIONS.md: could not read the file from the PR head"
    ]
