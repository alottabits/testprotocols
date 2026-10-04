"""Ratchet: explicit ``Any`` in the shipped packages may only go down.

Counts, by AST, every use of ``Any`` as a name or as ``typing.Any`` /
``t.Any`` / ``typing_extensions.Any``, plus ``"Any"`` appearing inside a string
literal that is not a docstring (for example ``cast("Any", x)``). Import
statements, docstrings and comments are not counted.

Ceilings measured 2026-10-04 when the ratchet was introduced: testprotocols 40,
testoperations 7. A task that removes an
``Any`` lowers the constant; none may raise it.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

TESTPROTOCOLS_CEILING = 40
TESTOPERATIONS_CEILING = 7

_ROOT = Path(__file__).resolve().parents[2]
_ANY_WORD = re.compile(r"\bAny\b")


def _docstring_nodes(tree: ast.AST) -> set[int]:
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            first = node.body[0] if node.body else None
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                ids.add(id(first.value))
    return ids


def count_any(source: str) -> int:
    tree = ast.parse(source)
    docstrings = _docstring_nodes(tree)
    total = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "Any":
            total += 1
        elif (
            isinstance(node, ast.Attribute)
            and node.attr == "Any"
            and isinstance(node.value, ast.Name)
            and node.value.id in {"typing", "t", "typing_extensions"}
        ):
            total += 1
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
            and _ANY_WORD.search(node.value)
        ):
            total += 1
    return total


def _count_package(package: str) -> int:
    src = _ROOT / package / "src"
    return sum(count_any(p.read_text()) for p in sorted(src.rglob("*.py")))


def test_count_any_rules() -> None:
    source = (
        '"""Any in a docstring."""\n'
        "import typing\n"
        "from typing import Any\n"
        "# Any in a comment\n"
        "a: Any = 1\n"
        "b: typing.Any = 2\n"
        'c = cast("Any", 3)\n'
    )
    assert count_any(source) == 3


def test_testprotocols_explicit_any_does_not_grow() -> None:
    assert _count_package("testprotocols") <= TESTPROTOCOLS_CEILING


def test_testoperations_explicit_any_does_not_grow() -> None:
    assert _count_package("testoperations") <= TESTOPERATIONS_CEILING
