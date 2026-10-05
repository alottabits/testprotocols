"""Second line of defence behind mypy's ``disallow_any_explicit`` (pyright has no such rule).

The only exempt ``Any`` is on a released signature whose line carries one of the
``EXEMPT_MARKERS``. Non-exempt ``Any`` has a ceiling of 0 in both packages, and the number
of exempted lines is pinned per class, so a new exemption cannot be added silently: it
needs a reviewed change to a constant. Class (a), ``DEPRECATED_MARKER``, is a deprecated
member and goes to 0 at the removal release; class (b), ``COMPATIBILITY_MARKERS``, is a
live released signature that is not deprecated: implementers declare their own types
(``COMPATIBILITY_MARKER``), or vendors extend the parameter model, so the contract does not
enumerate it (``VENDOR_MODEL_MARKER``, the TR-069 RPCs).

Counts, by AST, every use of ``Any`` as a name (including a name imported under an
alias, ``from typing import Any as A``) or as an attribute of the ``typing`` /
``typing_extensions`` modules (including ``import typing as t`` then ``t.Any``), plus
``"Any"`` as the first argument of ``cast`` / ``typing.cast``. Import statements,
docstrings, comments and other strings are not counted.

A line counts as exempt when it carries the marker; an ``Any`` on a multi-line signature
is exempt when the ``def`` line that opens it carries the marker, which is where mypy
reports it.

``object`` used as a type is counted the same way, because it is as imprecise as ``Any``
in a signature or field (no checker flags it, so this test is the only line of defence).
The rule, by AST: every ``object`` name inside

- a parameter or return annotation of a function or method,
- an annotated assignment at class or module level (a field), or
- a module-level type alias (a ``type`` statement, or an assignment of a subscripted type),

including inside a generic (``list[object]``, ``Mapping[str, object]``), in a public scope.
A scope is private when its function name starts with ``_`` and is not a dunder, when it is
inside a class whose name starts with ``_``, or when it is a module-level function or alias
of a module whose name starts with ``_``; a public class in a private module counts, because
a public record can inherit it. Not counted: the parameter of ``__eq__``, ``__ne__`` and
``__contains__`` (the data model types it ``object``), and every ``object`` outside an
annotation (a base class, an ``isinstance`` or ``cast`` argument, a local variable's
annotation inside a function body). Non-exempt ``object`` has a ceiling of 0 in both
packages; the exempt lines carry one of ``OBJECT_MARKERS`` and are pinned per class and
package: (a) ``OBJECT_DEPRECATED_MARKER``, a deprecated form, which goes at its removal
release; (b) ``OBJECT_OPEN_VALUE_MARKER``, a live open value the contract does not
enumerate (a vendor-extended option map, a decoder's packet bag).
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
#     A live released signature over a parameter model that vendors extend (TR-069).
VENDOR_MODEL_MARKER = (
    "# type: ignore[explicit-any]  # released signature kept: vendors extend the parameter model"
)
TESTPROTOCOLS_DEPRECATED_EXEMPT_LINES = 9
TESTPROTOCOLS_COMPATIBILITY_EXEMPT_LINES = 16
#     A live released return whose implementers return their own types (the consoles of
#     ``HwConsole``); the narrowing to a contract type is announced.
RETURN_COMPATIBILITY_MARKER = (
    "# type: ignore[explicit-any]  # released return kept: implementers return their own types"
)

# ``object`` used as a type: (a) a deprecated form, removed with it; (b) a live open value.
OBJECT_DEPRECATED_MARKER = "# object: deprecated form kept until removal"
OBJECT_OPEN_VALUE_MARKER = "# object: open value: the contract does not enumerate it"
OBJECT_MARKERS = (OBJECT_DEPRECATED_MARKER, OBJECT_OPEN_VALUE_MARKER)
OBJECT_CEILING = 0
OBJECT_EXEMPT_LINES = {
    ("testprotocols", OBJECT_DEPRECATED_MARKER): 4,
    ("testprotocols", OBJECT_OPEN_VALUE_MARKER): 3,
    ("testoperations", OBJECT_DEPRECATED_MARKER): 6,
    ("testoperations", OBJECT_OPEN_VALUE_MARKER): 0,
}

COMPATIBILITY_MARKERS = (COMPATIBILITY_MARKER, VENDOR_MODEL_MARKER, RETURN_COMPATIBILITY_MARKER)
EXEMPT_MARKERS = (DEPRECATED_MARKER, *COMPATIBILITY_MARKERS)

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


_OBJECT_DUNDER_PARAMETERS = {"__eq__", "__ne__", "__contains__"}


def _is_private(name: str) -> bool:
    return name.startswith("_") and not (name.startswith("__") and name.endswith("__"))


def _object_names(node: ast.AST | None) -> list[int]:
    if node is None:
        return []
    return [n.lineno for n in ast.walk(node) if isinstance(n, ast.Name) and n.id == "object"]


def _function_object_lines(func: ast.FunctionDef | ast.AsyncFunctionDef) -> list[int]:
    lines = _object_names(func.returns)
    if func.name in _OBJECT_DUNDER_PARAMETERS:
        return lines
    a = func.args
    for arg in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg]:
        if arg is not None:
            lines += _object_names(arg.annotation)
    return lines


def _object_lines(source: str, *, private_module: bool = False) -> list[tuple[int, int]]:
    """``(line, marker line)`` of every ``object`` used as a type in a public scope."""
    tree = ast.parse(source)
    found: list[tuple[int, int]] = []

    def scope(body: list[ast.stmt], *, module: bool) -> None:
        for node in body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                if _is_private(node.name) or (module and private_module):
                    continue
                found.extend((line, node.lineno) for line in _function_object_lines(node))
            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith("_"):
                    scope(node.body, module=False)
            elif isinstance(node, ast.AnnAssign):
                found.extend((line, line) for line in _object_names(node.annotation))
            elif module and not private_module and isinstance(node, ast.TypeAlias):
                found.extend((line, line) for line in _object_names(node.value))
            elif module and not private_module and isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Subscript):
                    found.extend((line, line) for line in _object_names(node.value))

    scope(tree.body, module=True)
    return found


def _split_object(source: str, *, private_module: bool = False) -> tuple[int, int]:
    """(non-exempt, exempt) counts of ``object`` used as a type."""
    text = source.splitlines()
    exempt = plain = 0
    for _, marker_line in _object_lines(source, private_module=private_module):
        if any(m in text[marker_line - 1] for m in OBJECT_MARKERS):
            exempt += 1
        else:
            plain += 1
    return plain, exempt


def _module_sources(package: str) -> list[tuple[bool, str]]:
    src = _ROOT / package / "src"
    return [
        (p.stem.startswith("_") and p.stem != "__init__", p.read_text())
        for p in sorted(src.rglob("*.py"))
    ]


def _count_object_package(package: str) -> int:
    return sum(
        _split_object(s, private_module=private)[0] for private, s in _module_sources(package)
    )


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
        sum(_exempt_lines("testprotocols", m) for m in COMPATIBILITY_MARKERS)
        == TESTPROTOCOLS_COMPATIBILITY_EXEMPT_LINES
    )


def test_object_rule() -> None:
    source = (
        "from collections.abc import Mapping\n"
        "class Base(object):\n"  # a base class: not counted
        "    a: object\n"  # a field: counted
        "    b: Mapping[str, object]\n"  # inside a generic: counted
        "    def f(self, x: object) -> list[object]:\n"  # parameter and return: 2
        "        y: object = x\n"  # a local variable: not counted
        "        return [y] if isinstance(y, object) else []\n"  # isinstance: not counted
        "    def __eq__(self, other: object) -> bool: ...\n"  # data-model parameter: not
        "    def _helper(self, x: object) -> object: ...\n"  # private: not counted
        "class _Private:\n"
        "    c: object\n"  # private class: not counted
        "type Alias = list[object]\n"  # a type alias: counted
        "Plain = dict[str, object]\n"  # an assigned alias: counted
        "def g(x: object) -> None: ...\n"  # a module function: counted
    )
    assert _split_object(source) == (7, 0)
    # in a private module the module-level function and aliases are private; classes count
    assert _split_object(source, private_module=True) == (4, 0)


def test_a_marked_signature_exempts_its_object() -> None:
    source = (
        f"def f(  {OBJECT_DEPRECATED_MARKER}\n"
        "    x: object,\n"
        ") -> object: ...\n"
        f"x: object  {OBJECT_OPEN_VALUE_MARKER}\n"
        "y: object\n"
    )
    assert _split_object(source) == (1, 3)


def test_no_unexempted_object_in_either_package() -> None:
    assert _count_object_package("testprotocols") <= OBJECT_CEILING
    assert _count_object_package("testoperations") <= OBJECT_CEILING


def test_the_object_exempted_lines_are_pinned_per_class() -> None:
    for (package, marker), pinned in OBJECT_EXEMPT_LINES.items():
        assert _exempt_lines(package, marker) == pinned, (package, marker)
