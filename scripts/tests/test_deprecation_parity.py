"""Tests for scripts/deprecation_parity.py."""

from __future__ import annotations

from pathlib import Path

from deprecation_parity import deprecation_paragraph, normalise, problems

REPO = Path(__file__).resolve().parents[2]

SENTENCE = (
    "Deprecated: use read_value. Removal not before the first release 6 months after the "
    "release that deprecates it."
)
GAUGE = f'''\
from typing import Protocol

from testprotocols._compat import deprecated


class Gauge(Protocol):
    @deprecated(
        "{SENTENCE}",
        category=None,
    )
    def get_value(self) -> str:
        """Return the value as text.

        Deprecated: use :meth:`read_value`. Removal not before the first release 6 months
        after the release that deprecates it.
        """
        ...

    def read_value(self) -> int:
        """Return the value."""
        ...

    def set_value(self, value: str) -> None:
        """Set the value. *value* as text is deprecated: pass an int."""
        ...

    def get_unit(self) -> str:
        """Return the unit."""
        ...
'''
REGISTER = """\
# Deprecation register

**testprotocols**

| item | replacement | kind | deprecated in | earliest removal |
| --- | --- | --- | --- | --- |
| `testprotocols.gauge:Gauge.get_value` | `read_value` | member | next release | later |
| `Gauge.set_value(value)`: `str` | `int` | parameter | next release | later |
"""


def write_tree(root: Path, gauge: str = GAUGE, register: str = REGISTER) -> Path:
    src = root / "packages" / "testprotocols" / "src" / "testprotocols"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("", encoding="utf-8")
    (src / "gauge.py").write_text(gauge, encoding="utf-8")
    (root / "packages" / "testprotocols" / "DEPRECATIONS.md").write_text(register, "utf-8")
    return root


def test_the_repository_is_consistent() -> None:
    assert problems(REPO) == []


def test_a_consistent_tree_passes(tmp_path: Path) -> None:
    assert problems(write_tree(tmp_path)) == []


def test_normalise_drops_markup() -> None:
    assert normalise("use :meth:`~x.read`  now") == "use x.read now"
    assert deprecation_paragraph("Text.\n\nDeprecated: go.\n  Later.\n\nMore.") == (
        "Deprecated: go.\n  Later."
    )


def test_marker_and_docstring_must_agree(tmp_path: Path) -> None:
    gauge = GAUGE.replace("Removal not before the first release 6 months\n", "Removal soon\n")
    found = problems(write_tree(tmp_path, gauge=gauge))
    assert len(found) == 1
    assert "gauge.py:" in found[0] and "differs from the docstring" in found[0]


def test_a_marked_member_needs_a_row(tmp_path: Path) -> None:
    register = REGISTER.replace("`testprotocols.gauge:Gauge.get_value`", "`Gauge.other`")
    found = problems(write_tree(tmp_path, register=register))
    assert any("no row of" in p and "Gauge.get_value" in p for p in found)


def test_a_member_row_names_a_marked_member(tmp_path: Path) -> None:
    register = REGISTER + "| `Gauge.get_unit` | none | member | next release | later |\n"
    found = problems(write_tree(tmp_path, register=register))
    assert found == [
        "packages/testprotocols/DEPRECATIONS.md:9: member row names `Gauge.get_unit`, "
        "which carries no @deprecated (precise-types-design.md, rule C2)"
    ]


def test_a_parameter_row_needs_the_docstring_to_state_it(tmp_path: Path) -> None:
    gauge = GAUGE.replace(" *value* as text is deprecated: pass an int.", "")
    found = problems(write_tree(tmp_path, gauge=gauge))
    assert len(found) == 1 and "Gauge.set_value" in found[0]


def test_a_released_row_is_not_checked(tmp_path: Path) -> None:
    register = REGISTER + "| `Gauge.gone` | none | member | 0.1.0 | 0.2.0 |\n"
    assert problems(write_tree(tmp_path, register=register)) == []
