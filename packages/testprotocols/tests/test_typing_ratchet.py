"""Second line of defence behind mypy's ``disallow_any_explicit`` (pyright has no such rule).

The only exempt ``Any`` is a released signature kept for the deprecation period; its
line carries ``EXEMPT_MARKER``. Non-exempt ``Any`` has a ceiling of 0 in both packages,
and the number of exempted lines is pinned per class, so a new exemption cannot be added
silently: it needs a reviewed change to a constant. Class (a), ``DEPRECATED_MARKER``, is a
deprecated member and goes to 0 at the removal release; class (b), ``COMPATIBILITY_MARKER``,
is a live released parameter that implementers declare with their own types.

Counts, by AST, every use of ``Any`` as a name (including a name imported under an
alias, ``from typing import Any as A``) or as an attribute of the ``typing`` /
``typing_extensions`` modules (including ``import typing as t`` then ``t.Any``), plus
``"Any"`` as the first argument of ``cast`` / ``typing.cast``. Import statements,
docstrings, comments and other strings are not counted.

A line counts as exempt when it carries the marker; an ``Any`` on a multi-line signature
is exempt when the ``def`` line that opens it carries the marker, which is where mypy
reports it.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

TESTPROTOCOLS_CEILING = 0
TESTOPERATIONS_CEILING = 0
# (a) a member deprecated in this release: the exemption ends with the member.
DEPRECATED_MARKER = "# type: ignore[explicit-any]  # released signature kept until removal"
# (b) a live released member whose implementers declare their own types (contravariant
#     parameters, invariant ``dict``), so no precise type can accept those declarations.
COMPATIBILITY_MARKER = (
    "# type: ignore[explicit-any]  # released parameter kept: implementers declare their own types"
)
EXEMPT_MARKERS = (DEPRECATED_MARKER, COMPATIBILITY_MARKER)
TESTPROTOCOLS_DEPRECATED_EXEMPT_LINES = 20
TESTPROTOCOLS_COMPATIBILITY_EXEMPT_LINES = 2

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


def _any_lines(source: str) -> list[int]:
    """The line of every explicit ``Any`` (one entry per use)."""
    tree = ast.parse(source)
    any_names, module_names = _aliases(tree)
    cast_strings = _cast_string_arguments(tree)
    lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in any_names:
            lines.append(node.lineno)
        elif (
            isinstance(node, ast.Attribute)
            and node.attr == "Any"
            and isinstance(node.value, ast.Name)
            and node.value.id in module_names
        ):
            lines.append(node.lineno)
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) in cast_strings
            and _ANY_WORD.search(node.value)
        ):
            lines.append(node.lineno)
    # ``Callable[..., X]``: the ``...`` is an implicit ``Any`` (mypy rejects it too)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.slice, ast.Tuple)
            and node.slice.elts
            and isinstance(node.slice.elts[0], ast.Constant)
            and node.slice.elts[0].value is Ellipsis
            and (
                (isinstance(node.value, ast.Name) and node.value.id == "Callable")
                or (isinstance(node.value, ast.Attribute) and node.value.attr == "Callable")
            )
        ):
            lines.append(node.lineno)
    return lines


def _signature_start(tree: ast.AST, lineno: int) -> int:
    """The ``def`` line of the signature holding *lineno*, else *lineno* itself."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if node.lineno <= lineno < node.body[0].lineno:
                return node.lineno
    return lineno


def _split(source: str) -> tuple[int, int]:
    """(non-exempt, exempt) counts of explicit ``Any``."""
    tree = ast.parse(source)
    text = source.splitlines()
    exempt = 0
    plain = 0
    for lineno in _any_lines(source):
        if any(m in text[_signature_start(tree, lineno) - 1] for m in EXEMPT_MARKERS):
            exempt += 1
        else:
            plain += 1
    return plain, exempt


def count_any(source: str) -> int:
    """The explicit ``Any`` that no marker exempts."""
    return _split(source)[0]


def _exempt_signature_lines(source: str, marker: str) -> int:
    """How many ``def`` lines the source marks with *marker*."""
    return sum(marker in line for line in source.splitlines())


def _sources(package: str) -> list[str]:
    src = _ROOT / package / "src"
    return [p.read_text() for p in sorted(src.rglob("*.py"))]


def _count_package(package: str) -> int:
    return sum(count_any(s) for s in _sources(package))


def _exempt_lines(package: str, marker: str) -> int:
    return sum(_exempt_signature_lines(s, marker) for s in _sources(package))


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


def test_a_marked_signature_exempts_its_any() -> None:
    source = (
        "from typing import Any\n"
        "def f(\n"
        "    a: Any,\n"
        ") -> None: ...\n"
        f"def g(a: Any) -> None: ...  {COMPATIBILITY_MARKER}\n"
        f"def h(\n"
        "    a: Any,\n"
        "    b: Any,\n"
        f") -> None: ...\n"
    )
    assert _split(source) == (3, 1)
    marked = source.replace("def f(\n", f"def f(  {DEPRECATED_MARKER}\n")
    assert _split(marked) == (2, 2)


def test_an_ellipsis_callable_counts_as_any() -> None:
    source = (
        "from collections.abc import Callable\n"
        "import collections.abc as c\n"
        "a: Callable[..., int]\n"
        "b: c.Callable[..., int]\n"
        "d: Callable[[int], int]\n"
        "e: Callable[[...], int]\n"
    )
    # a and b count; d is precise; e is not valid typing and is not counted
    assert count_any(source) == 2


def test_testprotocols_has_no_unexempted_explicit_any() -> None:
    assert _count_package("testprotocols") <= TESTPROTOCOLS_CEILING


def test_testoperations_has_no_unexempted_explicit_any() -> None:
    assert _count_package("testoperations") <= TESTOPERATIONS_CEILING


def test_testoperations_exempts_nothing() -> None:
    assert all(_exempt_lines("testoperations", m) == 0 for m in EXEMPT_MARKERS)


def test_the_exempted_lines_are_pinned_per_class() -> None:
    assert (
        _exempt_lines("testprotocols", DEPRECATED_MARKER) == TESTPROTOCOLS_DEPRECATED_EXEMPT_LINES
    )
    assert (
        _exempt_lines("testprotocols", COMPATIBILITY_MARKER)
        == TESTPROTOCOLS_COMPATIBILITY_EXEMPT_LINES
    )
