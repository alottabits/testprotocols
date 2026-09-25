"""Tests for scripts/changelog_section.py."""

from __future__ import annotations

from pathlib import Path

import pytest
from changelog_section import SectionError, main, section, version_problems

UNRELEASED = (
    "# Changelog\n\nIntro.\n\n## [Unreleased]\n\n"
    "### testprotocols\n\n- no entries yet\n\n### testoperations\n\n- no entries yet\n\n"
)
ENTRY = (
    "#### Added\n\n"
    "- **operation** `testoperations.homing:set_subnet_advertised` — flip one\n"
    "  overlay subnet in place. No proposal; PR #28."
)
BUMP = "- no API change (version bump only)"


def body(tp: str, to: str) -> str:
    return f"### testprotocols\n\n{tp}\n\n### testoperations\n\n{to}"


def released(version: str, tp: str, to: str, *, head: str = "— 2026-09-21") -> str:
    return f"## [{version}] {head}\n\n{body(tp, to)}\n\n"


def test_section_in_the_middle() -> None:
    text = UNRELEASED + released("0.13.0", ENTRY, BUMP) + released("0.12.1", BUMP, ENTRY)
    assert section(text, "0.13.0") == body(ENTRY, BUMP)


def test_section_at_the_end() -> None:
    text = UNRELEASED + released("0.13.0", ENTRY, BUMP) + released("0.12.1", BUMP, ENTRY)
    assert section(text, "0.12.1") == body(BUMP, ENTRY)


def test_hyphen_heading() -> None:
    text = UNRELEASED + released("0.13.0", ENTRY, ENTRY, head="- 2026-09-21")
    assert section(text, "0.13.0") == body(ENTRY, ENTRY)


def test_heading_may_carry_a_suffix() -> None:
    text = UNRELEASED + released("0.12.1", ENTRY, BUMP, head="— 2026-09-09 [YANKED]")
    assert section(text, "0.12.1") == body(ENTRY, BUMP)


def test_en_dash_heading_is_not_a_heading() -> None:
    text = UNRELEASED + released("0.13.0", ENTRY, BUMP, head="– 2026-09-21")  # noqa: RUF001
    with pytest.raises(SectionError, match=r"^has no `## \[0\.13\.0\] — YYYY-MM-DD` heading$"):
        section(text, "0.13.0")
    undated = UNRELEASED + released("0.13.0", ENTRY, BUMP, head="")
    with pytest.raises(SectionError, match=r"heading"):
        section(undated, "0.13.0")


def test_heading_missing() -> None:
    with pytest.raises(SectionError, match=r"^has no `## \[0\.13\.0\] — YYYY-MM-DD` heading$"):
        section(UNRELEASED, "0.13.0")


def test_version_must_match_whole_and_be_x_y_z() -> None:
    text = UNRELEASED + released("10.13.0", ENTRY, BUMP)
    with pytest.raises(SectionError, match="has no"):
        section(text, "0.13.0")
    with pytest.raises(SectionError, match=r"^version must be X\.Y\.Z: '0\.13\.0rc1'$"):
        section(text, "0.13.0rc1")


def test_duplicate_heading_is_refused() -> None:
    text = UNRELEASED + released("0.13.0", ENTRY, BUMP) + released("0.13.0", BUMP, ENTRY)
    with pytest.raises(SectionError, match=r"^heading `## \[0\.13\.0\]` appears 2 times$"):
        section(text, "0.13.0")


def test_empty_section() -> None:
    nothing = UNRELEASED + "## [0.13.0] — 2026-09-21\n\n" + released("0.12.1", ENTRY, BUMP)
    with pytest.raises(SectionError, match=r"^is empty$"):
        section(nothing, "0.13.0")
    headings_only = UNRELEASED + "## [0.13.0] — 2026-09-21\n\n### testprotocols\n\n#### Added\n"
    with pytest.raises(SectionError, match=r"^is empty$"):
        section(headings_only, "0.13.0")


def test_no_entries_yet_left_in() -> None:
    text = UNRELEASED + released("0.13.0", ENTRY, "- no entries yet")
    with pytest.raises(SectionError, match=r"^still contains `- no entries yet`$"):
        section(text, "0.13.0")


def test_version_bump_only_everywhere_is_refused_unless_allowed() -> None:
    text = UNRELEASED + released("0.13.0", BUMP, BUMP)
    with pytest.raises(
        SectionError,
        match=r"^has no entry beyond `- no API change \(version bump only\)`$",
    ):
        section(text, "0.13.0")
    assert section(text, "0.13.0", allow_empty=True) == body(BUMP, BUMP)


def test_one_package_version_bump_only_is_accepted() -> None:
    text = UNRELEASED + released("0.13.0", BUMP, ENTRY)
    assert section(text, "0.13.0") == body(BUMP, ENTRY)


def test_indented_dash_is_not_an_entry() -> None:
    text = UNRELEASED + released("0.13.0", BUMP, BUMP + "\n  - a continuation, not an entry")
    with pytest.raises(SectionError, match="has no entry beyond"):
        section(text, "0.13.0")


def write_versions(root: Path, tp: str, to: str) -> None:
    for name, version in (("testprotocols", tp), ("testoperations", to)):
        path = root / "packages" / name / "pyproject.toml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'[project]\nname = "{name}"\nversion = "{version}"\n', encoding="utf-8")


def test_version_problems(tmp_path: Path) -> None:
    write_versions(tmp_path, "0.13.0", "0.13.0")
    assert version_problems(tmp_path, "0.13.0") == []
    write_versions(tmp_path, "0.13.0", "0.12.1")
    assert version_problems(tmp_path, "0.13.0") == [
        "packages/testoperations/pyproject.toml: version is 0.12.1, tag says 0.13.0"
    ]
    assert version_problems(tmp_path, "0.13.0", source="title") == [
        "packages/testoperations/pyproject.toml: version is 0.12.1, title says 0.13.0"
    ]


def test_cli_prints_the_section(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(UNRELEASED + released("0.13.0", ENTRY, BUMP), encoding="utf-8")
    write_versions(tmp_path, "0.13.0", "0.13.0")
    assert main(["0.13.0", "--file", str(changelog), "--check-versions"]) == 0
    out = capsys.readouterr()
    assert out.out == body(ENTRY, BUMP) + "\n"
    assert out.err == ""


def test_cli_refusals(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(UNRELEASED + released("0.13.0", BUMP, BUMP), encoding="utf-8")
    assert main(["0.13.0", "--file", str(changelog)]) == 1
    out = capsys.readouterr()
    assert out.out == ""
    assert out.err == (
        f"{changelog}: released section has no entry beyond `- no API change (version bump only)`\n"
    )
    assert main(["0.13.0", "--file", str(changelog), "--allow-empty"]) == 0
    assert capsys.readouterr().out == body(BUMP, BUMP) + "\n"

    write_versions(tmp_path, "0.12.1", "0.13.0")
    code = main(["0.13.0", "--file", str(changelog), "--allow-empty", "--check-versions"])
    assert code == 1
    out = capsys.readouterr()
    assert out.out == ""
    assert out.err == "packages/testprotocols/pyproject.toml: version is 0.12.1, tag says 0.13.0\n"


def test_cli_missing_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = tmp_path / "CHANGELOG.md"
    assert main(["0.13.0", "--file", str(missing)]) == 1
    assert capsys.readouterr().err == f"{missing}: cannot read the file\n"

    missing.write_text(UNRELEASED + released("0.13.0", ENTRY, BUMP), encoding="utf-8")
    assert main(["0.13.0", "--file", str(missing), "--check-versions"]) == 1
    assert capsys.readouterr().err == (
        "packages/testprotocols/pyproject.toml: cannot read a [project] version\n"
        "packages/testoperations/pyproject.toml: cannot read a [project] version\n"
    )
