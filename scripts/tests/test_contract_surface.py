"""Tests for scripts/contract_surface.py."""

from __future__ import annotations

from pathlib import Path

import pytest
from contract_surface import (
    BREAKING,
    CONSUMER,
    Change,
    check_changelog,
    diff,
    direction,
    enum_param_problems,
    main,
    read_surface,
)

REPO = Path(__file__).resolve().parents[2]

MODELS_INIT = "from testprotocols.models.things import Mode, Rule\n"
THINGS = """\
from dataclasses import dataclass
from enum import StrEnum


class Mode(StrEnum):
    ON = "on"
    OFF = "off"


@dataclass
class Rule:
    name: str
    port: str = ""
"""
WIDGET = """\
from typing import Any, Protocol

from testprotocols.models import Mode


class Widget(Protocol):
    def read(self, name: str) -> dict[str, Any]: ...

    def set_mode(self, mode: str, *, force: bool = False) -> None: ...

    def ping(self, since: Any, count: int = 3) -> bool: ...
"""
OPS = """\
def run(widget: object, label: str = "a") -> int:
    return 0
"""


def tree(root: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def base_files() -> dict[str, str]:
    return {
        "packages/testprotocols/src/testprotocols/__init__.py": "",
        "packages/testprotocols/src/testprotocols/models/__init__.py": MODELS_INIT,
        "packages/testprotocols/src/testprotocols/models/things.py": THINGS,
        "packages/testprotocols/src/testprotocols/widget.py": WIDGET,
        "packages/testprotocols/src/testprotocols/_private.py": "class Hidden: ...\n",
        "packages/testoperations/src/testoperations/__init__.py": "",
        "packages/testoperations/src/testoperations/ops.py": OPS,
    }


def changes_between(tmp_path: Path, edits: dict[str, str]) -> list[Change]:
    base = tree(tmp_path / "base", base_files())
    head = tree(tmp_path / "head", base_files() | edits)
    return diff(read_surface(base), read_surface(head))


def kinds(changes: list[Change]) -> set[tuple[str, str]]:
    return {(c.classification, c.symbol) for c in changes}


def test_identical_trees_have_no_change(tmp_path: Path) -> None:
    assert changes_between(tmp_path, {}) == []


def test_the_repository_against_itself_is_empty() -> None:
    surface = read_surface(REPO)
    assert surface.symbols, "the repository's packages were not read"
    assert diff(surface, surface) == []


def test_reexported_models_display_at_the_package_path(tmp_path: Path) -> None:
    surface = read_surface(tree(tmp_path, base_files()))
    rule = surface.symbols["testprotocols.models.things:Rule"]
    assert rule.paths == {"testprotocols.models.things", "testprotocols.models"}
    assert "testprotocols._private:Hidden" not in surface.symbols


def test_protocol_member_changes_are_classified(tmp_path: Path) -> None:
    widget = (
        WIDGET.replace("-> dict[str, Any]", "-> dict[str, int]")
        .replace("mode: str,", "mode: Mode | str, quiet: bool = False,")
        .replace("force: bool = False", "force: bool = True, dry: bool = False")
        .replace("since: Any", "since: float | None")
        .replace("def ping", "def reset(self) -> None: ...\n\n    def ping")
    )
    changes = changes_between(
        tmp_path, {"packages/testprotocols/src/testprotocols/widget.py": widget}
    )
    by = {(c.classification, c.symbol): c for c in changes}
    path = "testprotocols.widget:Widget"
    assert ("added-member", f"{path}.reset") in by
    assert by[("added-member", f"{path}.reset")].needs == (BREAKING,)
    assert ("param-added-keyword-only", f"{path}.set_mode(dry)") in by
    assert ("param-added-defaulted", f"{path}.set_mode(quiet)") in by
    assert by[("param-annotation-changed", f"{path}.set_mode(mode)")].direction == "widened"
    assert not by[("param-annotation-changed", f"{path}.set_mode(mode)")].breaking
    assert by[("default-changed", f"{path}.set_mode(force)")].breaking
    since = by[("param-annotation-changed", f"{path}.ping(since)")]
    assert since.direction == "narrowed" and since.breaking
    assert by[("return-annotation-changed", f"{path}.read")].direction == "unknown"


def test_model_and_enum_changes_are_classified(tmp_path: Path) -> None:
    things = (
        THINGS.replace("@dataclass\nclass Rule", "@dataclass(frozen=True)\nclass Rule")
        .replace('    port: str = ""', '    port: str | None = ""\n    label: str = "x"')
        .replace('    OFF = "off"\n', '    AUTO = "auto"\n')
        .replace('ON = "on"', 'ON = "1"')
    )
    changes = changes_between(
        tmp_path, {"packages/testprotocols/src/testprotocols/models/things.py": things}
    )
    found = kinds(changes)
    assert ("model-frozen-changed", "testprotocols.models:Rule") in found
    assert ("field-annotation-changed", "testprotocols.models:Rule.port") in found
    assert ("field-added", "testprotocols.models:Rule.label") in found
    assert ("enum-member-removed", "testprotocols.models:Mode.OFF") in found
    assert ("enum-member-added", "testprotocols.models:Mode.AUTO") in found
    assert ("enum-value-changed", "testprotocols.models:Mode.ON") in found


def test_removed_and_renamed_members(tmp_path: Path) -> None:
    widget = WIDGET.replace("def read(", "def read_all(").replace(
        "    def ping(self, since: Any, count: int = 3) -> bool: ...\n", ""
    )
    found = kinds(
        changes_between(tmp_path, {"packages/testprotocols/src/testprotocols/widget.py": widget})
    )
    assert ("renamed?", "testprotocols.widget:Widget.read") in found
    assert ("removed-member", "testprotocols.widget:Widget.ping") in found


def test_operation_signatures_are_compared(tmp_path: Path) -> None:
    ops = OPS.replace('label: str = "a"', 'label: str = "b", *, host: str')
    found = kinds(
        changes_between(tmp_path, {"packages/testoperations/src/testoperations/ops.py": ops})
    )
    assert ("default-changed", "testoperations.ops:run(label)") in found
    assert ("param-added-required", "testoperations.ops:run(host)") in found


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("str", "Mode | str", "widened"),
        ("Mode | str", "Mode", "narrowed"),
        ("int", "Optional[int]", "widened"),
        ("Any", "datetime | None", "narrowed"),
        ("dict[str, Any]", "Mapping[str, object]", "unknown"),
        ("str | None", "None | str", "equal"),
    ],
)
def test_direction(old: str, new: str, expected: str) -> None:
    assert direction(old, new) == expected


CHANGELOG = """\
# Changelog

## [Unreleased]

### testprotocols

#### Breaking for driver authors

- **protocol member** `testprotocols.widget:Widget.reset() -> None` — new mandatory member.
  Migration: implement it. No proposal; PR #1.

#### Added

- **parameter** `testprotocols.widget:Widget.ping(since)` — narrowed. No proposal; PR #1.

### testoperations

- no entries yet
"""


def test_changelog_names_each_breaking_change(tmp_path: Path) -> None:
    widget = WIDGET.replace("since: Any", "since: float").replace(
        "def ping", "def reset(self) -> None: ...\n\n    def ping"
    )
    base = tree(tmp_path / "base", base_files())
    head = tree(
        tmp_path / "head",
        base_files() | {"packages/testprotocols/src/testprotocols/widget.py": widget},
    )
    head_surface = read_surface(head)
    changes = diff(read_surface(base), head_surface)
    problems = check_changelog(changes, CHANGELOG, head_surface, "CHANGELOG.md")
    # The new member is named under Breaking; the narrowed parameter only under Added.
    assert len(problems) == 1
    assert "Widget.ping(since)" in problems[0]
    assert f"{BREAKING} | {CONSUMER}" in problems[0]
    assert "packages/testprotocols/src/testprotocols/widget.py:" in problems[0]
    reset = next(c for c in changes if c.symbol.endswith("Widget.reset"))
    assert reset.covered_by == "CHANGELOG.md:9"


def test_new_member_takes_the_bare_enum(tmp_path: Path) -> None:
    widget = WIDGET.replace(
        "def ping",
        "def set_level(self, mode: Mode | str) -> None: ...\n\n"
        "    def set_bare(self, mode: Mode) -> None: ...\n\n    def ping",
    )
    base = read_surface(tree(tmp_path / "base", base_files()))
    head = read_surface(
        tree(
            tmp_path / "head",
            base_files() | {"packages/testprotocols/src/testprotocols/widget.py": widget},
        )
    )
    problems = enum_param_problems(base, head)
    assert len(problems) == 1
    assert "Widget.set_level(mode)" in problems[0] and "rule C4" in problems[0]
    # A released member that widens to E | str is a deprecation, not a new parameter.
    assert enum_param_problems(head, head) == []


def test_cli_on_identical_trees(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tree(tmp_path, base_files())
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(CHANGELOG, encoding="utf-8")
    argv = ["--base", str(root), "--head", str(root), "--check-changelog", str(changelog)]
    assert main([*argv, "--check-enum-params", "--format", "json"]) == 0
    assert '"changes": []' in capsys.readouterr().out
