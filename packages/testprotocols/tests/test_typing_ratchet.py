"""Ratchet: explicit ``Any`` in the shipped packages may only go down.

Counts, by AST, every use of ``Any`` as a name (including a name imported under an
alias, ``from typing import Any as A``) or as an attribute of the ``typing`` /
``typing_extensions`` modules (including ``import typing as t`` then ``t.Any``), plus
``"Any"`` as the first argument of ``cast`` / ``typing.cast``. Import statements,
docstrings, comments and other strings are not counted.

Ceilings re-measured 2026-10-04 after the blind spots were closed (no
change): testprotocols 40, testoperations 7. A task that removes an ``Any`` lowers the
constant; none may raise it.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

TESTPROTOCOLS_CEILING = 37
TESTOPERATIONS_CEILING = 7

_ROOT = Path(__file__).resolve().parents[2]
_ANY_WORD = re.compile(r"\bAny\b")


_TYPING_MODULES = {"typing", "typing_extensions"}


def _aliases(tree: ast.AST) -> tuple[set[str], set[str]]:
    """The names that mean ``Any`` and the names that mean the ``typing`` module."""
    any_names = {"Any"}
    module_names = set(_TYPING_MODULES)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in _TYPING_MODULES:
            any_names.update(a.asname or a.name for a in node.names if a.name == "Any")
        elif isinstance(node, ast.Import):
            module_names.update(
                a.asname for a in node.names if a.name in _TYPING_MODULES and a.asname
            )
    return any_names, module_names


def _cast_string_arguments(tree: ast.AST) -> set[int]:
    """Ids of the string constants that are the first argument of ``cast``."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and node.args):
            continue
        func = node.func
        is_cast = (isinstance(func, ast.Name) and func.id == "cast") or (
            isinstance(func, ast.Attribute) and func.attr == "cast"
        )
        first = node.args[0]
        if is_cast and isinstance(first, ast.Constant) and isinstance(first.value, str):
            ids.add(id(first))
    return ids


def count_any(source: str) -> int:
    tree = ast.parse(source)
    any_names, module_names = _aliases(tree)
    cast_strings = _cast_string_arguments(tree)
    total = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in any_names:
            total += 1
        elif (
            isinstance(node, ast.Attribute)
            and node.attr == "Any"
            and isinstance(node.value, ast.Name)
            and node.value.id in module_names
        ):
            total += 1
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) in cast_strings
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


def test_count_any_sees_aliases() -> None:
    source = (
        "import typing as t\n"
        "import typing_extensions as te\n"
        "from typing import Any as A\n"
        "from typing import Any as Anything, cast\n"
        "a: A = 1\n"
        "b: t.Any = 2\n"
        "c: te.Any = 3\n"
        "d: Anything = 4\n"
    )
    # one per use of an alias; the import statements themselves are not counted
    assert count_any(source) == 4


def test_count_any_counts_a_string_any_only_as_the_first_argument_of_cast() -> None:
    source = (
        "import typing\n"
        "from typing import cast\n"
        'a = cast("Any", 1)\n'
        'b = typing.cast("list[Any]", 2)\n'
        'c = cast(int, "Any")\n'
        'd = {"Any": 1}\n'
        'e = "Any is fine here"\n'
    )
    # a and b count; c, d and e do not
    assert count_any(source) == 2


def test_testprotocols_explicit_any_does_not_grow() -> None:
    assert _count_package("testprotocols") <= TESTPROTOCOLS_CEILING


def test_testoperations_explicit_any_does_not_grow() -> None:
    assert _count_package("testoperations") <= TESTOPERATIONS_CEILING
