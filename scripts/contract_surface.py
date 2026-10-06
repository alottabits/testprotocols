"""The contract surface of two source trees, the differences between them, and their records.

Reads ``packages/testprotocols/src`` and ``packages/testoperations/src`` of a *base* and a
*head* tree with :mod:`ast` only: nothing is imported or executed, and no git is needed, so
the trees can be two checked-out commits, two ``git archive`` extracts or two plain
directories.

The surface (CONTRIBUTING.md, "The contract checks"):

- every ``typing.Protocol`` class and its members: methods (parameter names, kinds,
  annotations and defaults as source text, return annotation), properties and attributes;
- every dataclass and ``NamedTuple``: its fields in order (annotation, default,
  keyword-only) and whether it is frozen;
- every ``Enum`` / ``StrEnum`` / ``IntEnum`` (any class with an enum base): member names
  and values;
- every other public class: its constructor, public methods and properties;
- public module-level type aliases;
- in ``testoperations``, the public functions of public modules.

A module, class, function or member whose name starts with ``_`` is private (a dunder
method is public only as ``__init__`` and ``__call__``). A symbol is listed once, at its
defining module; the package ``__init__`` modules that re-export it give it its other
public paths, which a changelog entry may use.

Each difference head vs base gets one classification (``CLASSIFICATIONS``); an annotation
change also gets a direction where it can be decided syntactically: a union superset is a
widening, a union subset a narrowing, ``Any`` / ``object`` is the widest type, and
anything else is ``unknown``. Whether a change is breaking follows from who it breaks:
an implementer of a protocol (a new member or parameter, a narrowed return) or a caller
(a removal, a narrowed parameter, a changed default, a reordered or newly required field,
a model newly frozen, a removed enum member).

``--check-changelog CHANGELOG.md`` requires every breaking change to be named by an
entry of the ``[Unreleased]`` section of that changelog, under the change's package and
one of the subsections the change needs (``NEEDS``). An entry names a change when its
subject (the text before its `` — ``) carries a ``module:Symbol`` code span whose module
is a public path of the change's symbol, names the class, and names the member, field,
parameter or enum member. A change on a member or class that carries ``@deprecated`` in
the head and has a row in the deprecation register is also covered by a *Deprecated*
entry naming it.

``--check-enum-params`` fails a protocol member that is new in the head (a member added to
a protocol, or a member of a new protocol) and takes a parameter annotated with an enum of
either package together with its raw ``str`` or ``int`` form: a new parameter has no
released form, so it takes the bare enum (``docs/architecture/precise-types-design.md``,
rule C4). ``OPEN_VOCABULARY`` lists the recorded exceptions.

Usage::

    python scripts/contract_surface.py --base BASE_DIR --head HEAD_DIR \\
        [--format json|md] [--check-changelog CHANGELOG.md] [--check-enum-params]

``--check-changelog`` reads the changelog relative to the current directory unless the
path is absolute; the register beside it is ``packages/testprotocols/DEPRECATIONS.md`` of
the head tree. The report goes to standard output; each failure is one line on standard
error, and the exit status is 1 when there is one.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

from changelog_entries import register_rows, unreleased

PACKAGES = ("testprotocols", "testoperations")
DEPRECATIONS = "packages/testprotocols/DEPRECATIONS.md"

CLASSIFICATIONS = (
    "added-member",
    "removed-member",
    "renamed?",
    "param-added-required",
    "param-added-keyword-only",
    "param-added-defaulted",
    "param-removed",
    "param-kind-changed",
    "param-annotation-changed",
    "return-annotation-changed",
    "default-changed",
    "field-added",
    "field-removed",
    "field-reordered",
    "field-annotation-changed",
    "model-frozen-changed",
    "enum-member-added",
    "enum-member-removed",
    "enum-value-changed",
    "alias-changed",
    "deprecated-marker-added",
)

BREAKING = "Breaking for driver authors"
CONSUMER = "Consumer action"
DEPRECATED = "Deprecated"
CHANGED = "Changed"
_ANY_BREAK = (BREAKING, CONSUMER)
_ANNOUNCED = (BREAKING, CONSUMER, DEPRECATED)
_UNKNOWN = (BREAKING, CONSUMER, DEPRECATED, CHANGED)

# Recorded exceptions to the rule that a new protocol member takes the bare enum: a
# parameter whose vocabulary vendors extend, so its raw word is part of the contract.
# Key: ``module:Class.member(parameter)``; value: where the decision is recorded.
OPEN_VOCABULARY: dict[str, str] = {
    "testprotocols.dns_client:DnsClient.resolve(record_type)": (
        "docs/architecture/precise-types-design.md, Host-tier records: an answer can hold a "
        "record type DnsRecordType does not name, so resolve takes DnsRecordType | str"
    ),
}

_ENUM_BASES = frozenset({"Enum", "StrEnum", "IntEnum", "Flag", "IntFlag", "ReprEnum"})
_TOP_TYPES = frozenset({"Any", "typing.Any", "object", "typing_extensions.Any"})
_PUBLIC_DUNDERS = frozenset({"__init__", "__call__"})


# --------------------------------------------------------------------------- surface


@dataclass(frozen=True)
class Param:
    name: str
    kind: str  # positional-only | positional | var-positional | keyword-only | var-keyword
    annotation: str | None
    default: str | None


@dataclass(frozen=True)
class Member:
    """A method, property or attribute of a class, or a module-level function."""

    name: str
    kind: str  # method | property | attribute | function
    line: int
    params: tuple[Param, ...] = ()
    returns: str | None = None
    deprecated: bool = False
    docstring: str = ""
    marker: str | None = None  # the @deprecated sentence


@dataclass(frozen=True)
class Field:
    name: str
    annotation: str
    default: str | None
    keyword_only: bool
    line: int


@dataclass(frozen=True)
class EnumMember:
    name: str
    value: str
    line: int


@dataclass
class Symbol:
    """A public class, function or type alias at its defining module."""

    package: str
    module: str
    name: str
    kind: str  # protocol | dataclass | namedtuple | enum | class | function | alias
    file: str
    line: int
    bases: tuple[str, ...] = ()
    frozen: bool = False
    deprecated: bool = False
    docstring: str = ""
    marker: str | None = None
    members: dict[str, Member] = field(default_factory=lambda: dict[str, Member]())
    fields: list[Field] = field(default_factory=lambda: list[Field]())
    enum_members: list[EnumMember] = field(default_factory=lambda: list[EnumMember]())
    value: str | None = None  # an alias's target, as source text
    function: Member | None = None
    paths: set[str] = field(default_factory=lambda: set[str]())  # every public module

    @property
    def key(self) -> str:
        return f"{self.module}:{self.name}"


@dataclass
class Surface:
    root: Path
    symbols: dict[str, Symbol]

    def enum_names(self) -> set[str]:
        return {s.name for s in self.symbols.values() if s.kind == "enum"}

    def by_name(self, name: str) -> list[Symbol]:
        return [s for s in self.symbols.values() if s.name == name]


def _text(node: ast.expr | None) -> str | None:
    return None if node is None else ast.unparse(node)


def _dotted(node: ast.expr) -> str:
    if isinstance(node, ast.Subscript):
        return _dotted(node.value)
    if isinstance(node, ast.Call):
        return _dotted(node.func)
    if isinstance(node, ast.Attribute):
        return f"{_dotted(node.value)}.{node.attr}"
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _last(node: ast.expr) -> str:
    return _dotted(node).rsplit(".", 1)[-1]


def _is_private(name: str) -> bool:
    return name.startswith("_") and name not in _PUBLIC_DUNDERS


def _deprecated_marker(decorators: Sequence[ast.expr]) -> tuple[bool, str | None]:
    for dec in decorators:
        if _last(dec) != "deprecated":
            continue
        if isinstance(dec, ast.Call) and dec.args:
            first = dec.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                return True, first.value
        return True, None
    return False, None


def _params(fn: ast.FunctionDef | ast.AsyncFunctionDef, drop_first: bool) -> tuple[Param, ...]:
    args = fn.args
    positional = [*args.posonlyargs, *args.args]
    defaults: list[ast.expr | None] = [None] * (len(positional) - len(args.defaults))
    defaults += list(args.defaults)
    out: list[Param] = []
    for i, (arg, default) in enumerate(zip(positional, defaults, strict=True)):
        if drop_first and i == 0:
            continue
        kind = "positional-only" if i < len(args.posonlyargs) else "positional"
        out.append(Param(arg.arg, kind, _text(arg.annotation), _text(default)))
    if args.vararg is not None:
        out.append(Param(args.vararg.arg, "var-positional", _text(args.vararg.annotation), None))
    for arg, kw_default in zip(args.kwonlyargs, args.kw_defaults, strict=True):
        out.append(Param(arg.arg, "keyword-only", _text(arg.annotation), _text(kw_default)))
    if args.kwarg is not None:
        out.append(Param(args.kwarg.arg, "var-keyword", _text(args.kwarg.annotation), None))
    return tuple(out)


def _function(fn: ast.FunctionDef | ast.AsyncFunctionDef, in_class: bool) -> Member:
    decorators = {_last(d) for d in fn.decorator_list}
    deprecated, marker = _deprecated_marker(fn.decorator_list)
    kind = "function"
    if in_class:
        kind = "property" if decorators & {"property", "cached_property"} else "method"
    drop_first = in_class and "staticmethod" not in decorators
    return Member(
        name=fn.name,
        kind=kind,
        line=fn.lineno,
        params=() if kind == "property" else _params(fn, drop_first),
        returns=_text(fn.returns),
        deprecated=deprecated,
        docstring=ast.get_docstring(fn) or "",
        marker=marker,
    )


def _class_kind(node: ast.ClassDef) -> str:
    bases = {_last(b) for b in node.bases}
    if "Protocol" in bases:
        return "protocol"
    if bases & _ENUM_BASES:
        return "enum"
    if "NamedTuple" in bases:
        return "namedtuple"
    if any(_last(d) == "dataclass" for d in node.decorator_list):
        return "dataclass"
    return "class"


def _dataclass_options(node: ast.ClassDef) -> tuple[bool, bool]:
    """(frozen, kw_only) of the ``@dataclass`` decorator."""
    for dec in node.decorator_list:
        if _last(dec) == "dataclass" and isinstance(dec, ast.Call):
            opts = {
                k.arg: k.value.value
                for k in dec.keywords
                if k.arg is not None and isinstance(k.value, ast.Constant)
            }
            return opts.get("frozen") is True, opts.get("kw_only") is True
    return False, False


def _field_default(value: ast.expr | None) -> tuple[str | None, bool]:
    """A field's default as source text, and whether ``field()`` makes it keyword-only."""
    if value is None:
        return None, False
    if isinstance(value, ast.Call) and _last(value.func) == "field":
        kw = {k.arg: k.value for k in value.keywords if k.arg is not None}
        kw_only = isinstance(kw.get("kw_only"), ast.Constant) and getattr(
            kw.get("kw_only"), "value", False
        )
        if "default" in kw:
            return ast.unparse(kw["default"]), bool(kw_only)
        if "default_factory" in kw:
            return f"<factory {ast.unparse(kw['default_factory'])}>", bool(kw_only)
        return None, bool(kw_only)
    return ast.unparse(value), False


def _class(node: ast.ClassDef, package: str, module: str, file: str) -> Symbol:
    kind = _class_kind(node)
    deprecated, marker = _deprecated_marker(node.decorator_list)
    sym = Symbol(
        package=package,
        module=module,
        name=node.name,
        kind=kind,
        file=file,
        line=node.lineno,
        bases=tuple(ast.unparse(b) for b in node.bases),
        deprecated=deprecated,
        docstring=_class_docstrings(node),
        marker=marker,
    )
    frozen, kw_only = _dataclass_options(node)
    sym.frozen = frozen
    kw_rest = kw_only
    for stmt in node.body:
        if isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):
            if _is_private(stmt.name) or any(
                isinstance(d, ast.Attribute) and d.attr in {"setter", "deleter"}
                for d in stmt.decorator_list
            ):
                continue
            if kind in {"dataclass", "namedtuple"} and stmt.name == "__init__":
                continue
            if kind == "protocol" and stmt.name == "__init__":
                continue
            sym.members[stmt.name] = _function(stmt, in_class=True)
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            name = stmt.target.id
            annotation = ast.unparse(stmt.annotation)
            if annotation.startswith(("ClassVar", "typing.ClassVar", "Final")):
                continue
            if _last(stmt.annotation) == "KW_ONLY":
                kw_rest = True
                continue
            if _is_private(name):
                continue
            if kind in {"dataclass", "namedtuple"}:
                default, field_kw = _field_default(stmt.value)
                sym.fields.append(
                    Field(name, annotation, default, kw_rest or field_kw, stmt.lineno)
                )
            elif kind in {"protocol", "class"}:
                sym.members[name] = Member(
                    name, "attribute", stmt.lineno, returns=annotation, docstring=""
                )
        elif kind == "enum" and isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    sym.enum_members.append(
                        EnumMember(target.id, ast.unparse(stmt.value), stmt.lineno)
                    )
    return sym


def _class_docstrings(node: ast.ClassDef) -> str:
    """The class docstring and every attribute docstring in its body, joined."""
    parts = [ast.get_docstring(node) or ""]
    for prev, stmt in zip(node.body, node.body[1:], strict=False):
        if (
            isinstance(prev, ast.AnnAssign | ast.Assign)
            and isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str)
        ):
            parts.append(stmt.value.value)
    return "\n\n".join(p for p in parts if p)


def _alias(stmt: ast.stmt) -> tuple[str, str, int] | None:
    if isinstance(stmt, ast.TypeAlias):
        return stmt.name.id, ast.unparse(stmt.value), stmt.lineno
    if (
        isinstance(stmt, ast.AnnAssign)
        and isinstance(stmt.target, ast.Name)
        and _last(stmt.annotation) == "TypeAlias"
        and stmt.value is not None
    ):
        return stmt.target.id, ast.unparse(stmt.value), stmt.lineno
    if (
        isinstance(stmt, ast.Assign)
        and len(stmt.targets) == 1
        and isinstance(stmt.targets[0], ast.Name)
    ):
        name = stmt.targets[0].id
        value = stmt.value
        type_like = isinstance(value, ast.Subscript) or (
            isinstance(value, ast.BinOp) and isinstance(value.op, ast.BitOr)
        )
        if type_like and name[:1].isupper() and not name.isupper():
            return name, ast.unparse(value), stmt.lineno
    return None


def _module_name(src: Path, path: Path) -> str:
    parts = list(path.relative_to(src).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _modules(root: Path, package: str) -> Iterator[tuple[str, Path]]:
    src = root / "packages" / package / "src"
    if not (src / package).is_dir():
        return
    for path in sorted((src / package).rglob("*.py")):
        yield _module_name(src, path), path


def _module_public(module: str) -> bool:
    return not any(part.startswith("_") for part in module.split("."))


def _reexports(module: str, is_package: bool, tree: ast.Module) -> dict[str, str]:
    """``name -> source module`` for each ``from … import name`` at module level.

    Read for package ``__init__`` modules only: a name a package imports is a public path
    of the symbol; a name an ordinary module imports is a dependency.
    """
    out: dict[str, str] = {}
    for stmt in tree.body:
        if not isinstance(stmt, ast.ImportFrom):
            continue
        if stmt.level:
            parts = module.split(".")
            keep = len(parts) - stmt.level + (1 if is_package else 0)
            source = ".".join([*parts[:keep], *([stmt.module] if stmt.module else [])])
        else:
            source = stmt.module or ""
        for alias in stmt.names:
            if alias.asname in (None, alias.name):
                out[alias.name] = source
    return out


def read_surface(root: Path) -> Surface:
    """The public contract surface of the tree at *root*."""
    symbols: dict[str, Symbol] = {}
    exports: dict[str, dict[str, str]] = {}
    for package in PACKAGES:
        for module, path in _modules(root, package):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            if path.name == "__init__.py":
                exports[module] = _reexports(module, True, tree)
            if not _module_public(module):
                continue
            file = path.relative_to(root).as_posix()
            for stmt in tree.body:
                sym: Symbol | None = None
                if isinstance(stmt, ast.ClassDef) and not _is_private(stmt.name):
                    sym = _class(stmt, package, module, file)
                elif (
                    package == "testoperations"
                    and isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef)
                    and not stmt.name.startswith("_")
                ):
                    fn = _function(stmt, in_class=False)
                    sym = Symbol(
                        package,
                        module,
                        stmt.name,
                        "function",
                        file,
                        stmt.lineno,
                        deprecated=fn.deprecated,
                        docstring=fn.docstring,
                        marker=fn.marker,
                        function=fn,
                    )
                elif (alias := _alias(stmt)) is not None and not alias[0].startswith("_"):
                    sym = Symbol(package, module, alias[0], "alias", file, alias[2], value=alias[1])
                if sym is not None:
                    sym.paths.add(module)
                    symbols[sym.key] = sym
    _add_reexport_paths(symbols, exports)
    return Surface(root, symbols)


def _add_reexport_paths(symbols: dict[str, Symbol], exports: dict[str, dict[str, str]]) -> None:
    def resolve(module: str, name: str, depth: int = 0) -> Symbol | None:
        if f"{module}:{name}" in symbols:
            return symbols[f"{module}:{name}"]
        source = exports.get(module, {}).get(name)
        if source is None or depth > 8:
            return None
        return resolve(source, name, depth + 1)

    for module, names in exports.items():
        if not _module_public(module):
            continue
        for name in names:
            sym = resolve(module, name)
            if sym is not None:
                sym.paths.add(module)


def display_path(sym: Symbol) -> str:
    """The path a changelog entry would use: the shortest public module below the root."""
    below_root = [p for p in sym.paths if "." in p] or sorted(sym.paths)
    return f"{min(below_root, key=lambda p: (p.count('.'), p))}:{sym.name}"


# --------------------------------------------------------------------------- annotations


def _union(text: str) -> frozenset[str]:
    try:
        node = ast.parse(text, mode="eval").body
    except SyntaxError:
        return frozenset({text})
    out: set[str] = set()

    def walk(n: ast.expr) -> None:
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.BitOr):
            walk(n.left)
            walk(n.right)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            try:
                walk(ast.parse(n.value, mode="eval").body)
            except SyntaxError:
                out.add(n.value)
        elif isinstance(n, ast.Subscript) and _last(n.value) in {"Optional", "Union"}:
            inner = n.slice
            for item in inner.elts if isinstance(inner, ast.Tuple) else [inner]:
                walk(item)
            if _last(n.value) == "Optional":
                out.add("None")
        else:
            out.add(ast.unparse(n))

    walk(node)
    return frozenset(out)


def direction(old: str | None, new: str | None) -> str:
    """``widened``, ``narrowed``, ``unknown`` or ``equal``: *new* against *old*.

    A missing annotation reads as ``Any``.
    """
    a = _union(old or "Any")
    b = _union(new or "Any")
    if a == b:
        return "equal"
    a_top, b_top = bool(a & _TOP_TYPES), bool(b & _TOP_TYPES)
    if a_top and not b_top:
        return "narrowed"
    if b_top and not a_top:
        return "widened"
    if a < b:
        return "widened"
    if b < a:
        return "narrowed"
    return "unknown"


def enum_or_raw(annotation: str | None, enums: set[str]) -> str | None:
    """The enum of an ``E | str`` / ``E | int`` annotation, else ``None``."""
    if annotation is None:
        return None
    members = _union(annotation)
    named = sorted(m.rsplit(".", 1)[-1] for m in members if m.rsplit(".", 1)[-1] in enums)
    if named and members & {"str", "int"}:
        return named[0]
    return None


# --------------------------------------------------------------------------- differences


@dataclass
class Change:
    classification: str
    package: str
    path: str  # module:Symbol, the display path of the owning symbol
    member: str | None  # the member, field or enum member; None for the symbol itself
    detail: str  # a short description
    file: str
    line: int
    direction: str | None = None
    breaking: bool = False
    needs: tuple[str, ...] = ()
    old: str | None = None
    new: str | None = None
    param: str | None = None  # the parameter, for a parameter change
    covered_by: str | None = None

    @property
    def symbol(self) -> str:
        path = self.path if self.member is None else f"{self.path}.{self.member}"
        return path if self.param is None else f"{path}({self.param})"

    def summary(self) -> str:
        what = self.classification
        if self.direction is not None and self.direction != "equal":
            what += f" ({self.direction})"
        if self.detail:
            what += f" [{self.detail}]"
        change = ""
        if self.old is not None or self.new is not None:
            change = f": {self.old or '-'} -> {self.new or '-'}"
        return f"{self.file}:{self.line}: {self.symbol} — {what}{change}"


def _member_owner_kind(sym: Symbol) -> str:
    return "protocol" if sym.kind == "protocol" else "callable"


def _needs(cls: str, owner: str, direction_: str | None = None, extra: str = "") -> tuple[str, ...]:
    """The changelog subsections one of which must name a change; ``()``: none needed."""
    if cls == "param-kind-changed" and extra == "symbol kind":
        return _UNKNOWN
    if cls in {"removed-member", "renamed?", "param-removed", "param-kind-changed"}:
        return _ANY_BREAK
    if cls in {"field-removed", "field-reordered", "enum-member-removed", "enum-value-changed"}:
        return _ANY_BREAK
    if cls == "added-member":
        return (BREAKING,) if owner == "protocol" else ()
    if cls == "param-added-required":
        return _ANY_BREAK
    if cls in {"param-added-keyword-only", "param-added-defaulted"}:
        return (BREAKING,) if owner == "protocol" else ()
    if cls == "default-changed":
        if extra == "default added":
            return (BREAKING,) if owner == "protocol" else ()
        return _UNKNOWN if extra == "not a literal" else _ANY_BREAK
    if cls == "param-annotation-changed":
        if direction_ == "narrowed" and extra == "from Any" and owner != "protocol":
            return _UNKNOWN
        return {"narrowed": _ANNOUNCED, "unknown": _UNKNOWN}.get(direction_ or "", ())
    if cls == "return-annotation-changed":
        if direction_ == "unknown":
            return _UNKNOWN
        if direction_ == "widened" or (direction_ == "narrowed" and owner == "protocol"):
            return _ANNOUNCED
        return ()
    if cls == "field-annotation-changed":
        return _UNKNOWN if direction_ == "unknown" else _ANNOUNCED
    if cls == "field-added":
        return _ANY_BREAK if extra == "required" else ()
    if cls == "model-frozen-changed":
        return _ANY_BREAK if extra == "frozen" else ()
    if cls == "alias-changed":
        return _UNKNOWN
    if cls == "deprecated-marker-added":
        return (DEPRECATED,)
    return ()


def _change(
    cls: str,
    sym: Symbol,
    member: str | None,
    detail: str,
    line: int,
    *,
    owner: str = "callable",
    direction_: str | None = None,
    extra: str = "",
    old: str | None = None,
    new: str | None = None,
    file: str | None = None,
    param: str | None = None,
) -> Change:
    needs = _needs(cls, owner, direction_, extra)
    return Change(
        classification=cls,
        package=sym.package,
        path=display_path(sym),
        member=member,
        detail=detail or extra,
        file=file or sym.file,
        line=line,
        direction=direction_,
        breaking=bool(needs),
        needs=needs,
        old=old,
        new=new,
        param=param,
    )


_ENUM_MEMBER = re.compile(r"^[A-Z]\w*\.[A-Z][A-Z0-9_]*$")


def _literal(text: str | None) -> bool:
    """Whether a default is decidable: a literal, or an ``Enum.MEMBER`` (never the literal)."""
    if text is None or _ENUM_MEMBER.match(text):
        return True
    try:
        ast.literal_eval(text)
    except (ValueError, SyntaxError, TypeError):
        return False
    return True


def _signature_text(m: Member) -> str:
    params = ", ".join(f"{p.name}: {p.annotation}" if p.annotation else p.name for p in m.params)
    return f"({params}) -> {m.returns}"


def _diff_params(
    base_sym: Symbol, head_sym: Symbol, old: Member, new: Member, owner: str, name: str | None
) -> Iterator[Change]:
    old_by = {p.name: p for p in old.params}
    new_by = {p.name: p for p in new.params}
    for p in old.params:
        if p.name not in new_by:
            yield _change(
                "param-removed",
                head_sym,
                name,
                "",
                new.line,
                owner=owner,
                param=p.name,
                old=p.annotation,
            )
    for p in new.params:
        if p.name in old_by:
            continue
        if p.kind in {"var-positional", "var-keyword"}:
            cls = "param-added-defaulted"
        elif p.default is None:
            cls = "param-added-required"
        elif p.kind == "keyword-only":
            cls = "param-added-keyword-only"
        else:
            cls = "param-added-defaulted"
        yield _change(
            cls, head_sym, name, "", new.line, owner=owner, param=p.name, new=p.annotation
        )
    old_pos = [p.name for p in old.params if p.kind in {"positional-only", "positional"}]
    new_pos = [p.name for p in new.params if p.kind in {"positional-only", "positional"}]
    for p in new.params:
        q = old_by.get(p.name)
        if q is None:
            continue
        moved = (
            p.name in old_pos
            and p.name in new_pos
            and old_pos.index(p.name) != new_pos.index(p.name)
        )
        if q.kind != p.kind or moved:
            yield _change(
                "param-kind-changed",
                head_sym,
                name,
                "",
                new.line,
                owner=owner,
                param=p.name,
                old=q.kind,
                new=p.kind,
            )
        d = direction(q.annotation, p.annotation)
        if d != "equal":
            from_any = bool(_union(q.annotation or "Any") & _TOP_TYPES)
            yield _change(
                "param-annotation-changed",
                head_sym,
                name,
                "",
                new.line,
                owner=owner,
                param=p.name,
                direction_=d,
                extra="from Any" if from_any else "",
                old=q.annotation,
                new=p.annotation,
            )
        if q.default != p.default:
            extra = (
                "default added"
                if q.default is None
                else "default removed"
                if p.default is None
                else ""
                if _literal(q.default) and _literal(p.default)
                else "not a literal"
            )
            yield _change(
                "default-changed",
                head_sym,
                name,
                "",
                new.line,
                owner=owner,
                param=p.name,
                extra=extra,
                old=q.default,
                new=p.default,
            )
    d = direction(old.returns, new.returns)
    if d != "equal":
        yield _change(
            "return-annotation-changed",
            head_sym,
            name,
            "",
            new.line,
            owner=owner,
            direction_=d,
            old=old.returns,
            new=new.returns,
        )
    if new.deprecated and not old.deprecated:
        yield _change("deprecated-marker-added", head_sym, name, "", new.line, owner=owner)


def _diff_members(base: Symbol, head: Symbol) -> Iterator[Change]:
    owner = _member_owner_kind(head)
    removed = {n: m for n, m in base.members.items() if n not in head.members}
    added = {n: m for n, m in head.members.items() if n not in base.members}
    renamed: dict[str, str] = {}
    for n, m in removed.items():
        twins = [a for a, am in added.items() if _signature_text(am) == _signature_text(m)]
        if len(twins) == 1 and twins[0] not in renamed.values():
            renamed[n] = twins[0]
    for n, m in removed.items():
        if n in renamed:
            yield _change(
                "renamed?",
                head,
                n,
                f"to {renamed[n]}",
                head.members[renamed[n]].line,
                owner=owner,
                old=n,
                new=renamed[n],
            )
        else:
            yield _change(
                "removed-member",
                head,
                n,
                "",
                m.line,
                owner=owner,
                file=base.file,
                old=_signature_text(m),
            )
    for n, m in added.items():
        if n not in renamed.values():
            yield _change("added-member", head, n, "", m.line, owner=owner, new=_signature_text(m))
    for n, new in head.members.items():
        old = base.members.get(n)
        if old is None:
            continue
        if old.kind != new.kind:
            yield _change(
                "param-kind-changed",
                head,
                n,
                "member kind",
                new.line,
                owner=owner,
                old=old.kind,
                new=new.kind,
            )
        if new.kind == "attribute" or old.kind == "attribute":
            d = direction(old.returns, new.returns)
            if d != "equal":
                yield _change(
                    "return-annotation-changed",
                    head,
                    n,
                    "",
                    new.line,
                    owner=owner,
                    direction_=d,
                    old=old.returns,
                    new=new.returns,
                )
            continue
        yield from _diff_params(base, head, old, new, owner, n)


def _diff_fields(base: Symbol, head: Symbol) -> Iterator[Change]:
    old_by = {f.name: f for f in base.fields}
    new_by = {f.name: f for f in head.fields}
    for f in base.fields:
        if f.name not in new_by:
            yield _change(
                "field-removed", head, f.name, "", f.line, file=base.file, old=f.annotation
            )
    for f in head.fields:
        if f.name not in old_by:
            yield _change(
                "field-added",
                head,
                f.name,
                "",
                f.line,
                extra="required" if f.default is None else "",
                new=f.annotation,
            )
    old_pos = [f.name for f in base.fields if not f.keyword_only]
    new_pos = [f.name for f in head.fields if not f.keyword_only]
    for f in head.fields:
        g = old_by.get(f.name)
        if g is None:
            continue
        if f.name in old_pos and (
            f.name not in new_pos or old_pos.index(f.name) != new_pos.index(f.name)
        ):
            yield _change(
                "field-reordered",
                head,
                f.name,
                "",
                f.line,
                old=str(old_pos.index(f.name)),
                new="keyword-only" if f.name not in new_pos else str(new_pos.index(f.name)),
            )
        d = direction(g.annotation, f.annotation)
        if d != "equal":
            yield _change(
                "field-annotation-changed",
                head,
                f.name,
                "",
                f.line,
                direction_=d,
                old=g.annotation,
                new=f.annotation,
            )
        if g.default != f.default:
            extra = (
                "default added"
                if g.default is None
                else ""
                if _literal(g.default) and _literal(f.default)
                else "not a literal"
            )
            yield _change(
                "default-changed",
                head,
                f.name,
                "",
                f.line,
                extra=extra,
                old=g.default,
                new=f.default,
            )


def _diff_enum(base: Symbol, head: Symbol) -> Iterator[Change]:
    old_by = {m.name: m for m in base.enum_members}
    new_by = {m.name: m for m in head.enum_members}
    for m in base.enum_members:
        if m.name not in new_by:
            yield _change(
                "enum-member-removed", head, m.name, "", m.line, file=base.file, old=m.value
            )
    for m in head.enum_members:
        old = old_by.get(m.name)
        if old is None:
            yield _change("enum-member-added", head, m.name, "", m.line, new=m.value)
        elif old.value != m.value:
            yield _change(
                "enum-value-changed", head, m.name, "", m.line, old=old.value, new=m.value
            )


def _diff_symbol(base: Symbol, head: Symbol) -> Iterator[Change]:
    owner = _member_owner_kind(head)
    if head.kind == "alias" and base.kind == "alias":
        d = direction(base.value, head.value)
        if d != "equal":
            yield _change(
                "alias-changed",
                head,
                None,
                "",
                head.line,
                direction_=d,
                old=base.value,
                new=head.value,
            )
        return
    if head.kind == "function" and base.function is not None and head.function is not None:
        yield from _diff_params(base, head, base.function, head.function, "callable", None)
        return
    if base.kind != head.kind:
        yield _change(
            "param-kind-changed",
            head,
            None,
            "",
            head.line,
            extra="symbol kind",
            old=base.kind,
            new=head.kind,
        )
    if base.frozen != head.frozen:
        yield _change(
            "model-frozen-changed",
            head,
            None,
            "",
            head.line,
            extra="frozen" if head.frozen else "unfrozen",
            old=str(base.frozen),
            new=str(head.frozen),
        )
    if head.deprecated and not base.deprecated:
        yield _change("deprecated-marker-added", head, None, "", head.line)
    if head.kind == "protocol" and base.kind == "protocol":
        old_bases, new_bases = set(base.bases), set(head.bases)
        for b in sorted(new_bases - old_bases):
            yield _change("added-member", head, None, f"base {b}", head.line, owner=owner, new=b)
        for b in sorted(old_bases - new_bases):
            yield _change("removed-member", head, None, f"base {b}", head.line, owner=owner, old=b)
    yield from _diff_members(base, head)
    yield from _diff_fields(base, head)
    yield from _diff_enum(base, head)


def diff(base: Surface, head: Surface) -> list[Change]:
    """Every difference of *head* against *base*, ordered by file and line."""
    changes: list[Change] = []
    for key, sym in base.symbols.items():
        if key not in head.symbols:
            changes.append(
                _change(
                    "removed-member", sym, None, f"{sym.kind} removed", sym.line, owner="callable"
                )
            )
    for key, sym in head.symbols.items():
        old = base.symbols.get(key)
        if old is None:
            changes.append(
                _change("added-member", sym, None, f"new {sym.kind}", sym.line, owner="callable")
            )
        else:
            changes.extend(_diff_symbol(old, sym))
    changes.sort(key=lambda c: (c.file, c.line, c.symbol, c.classification))
    return changes


def new_protocol_members(base: Surface, head: Surface) -> Iterator[tuple[Symbol, Member]]:
    """Each protocol member in *head* that *base* does not have (new protocols included)."""
    for key, sym in head.symbols.items():
        if sym.kind != "protocol":
            continue
        old = base.symbols.get(key)
        for name, member in sym.members.items():
            if old is None or old.kind != "protocol" or name not in old.members:
                yield sym, member


def enum_param_problems(base: Surface, head: Surface) -> list[str]:
    """New protocol members that take ``E | str`` (or ``E | int``) where ``E`` is an enum."""
    enums = head.enum_names()
    problems: list[str] = []
    for sym, member in new_protocol_members(base, head):
        for p in member.params:
            enum = enum_or_raw(p.annotation, enums)
            key = f"{display_path(sym)}.{member.name}({p.name})"
            if enum is None or key in OPEN_VOCABULARY:
                continue
            problems.append(
                f"{sym.file}:{member.line}: {key} — new member parameter typed "
                f"`{p.annotation}`: a new parameter has no released form, so it takes the "
                f"bare `{enum}` (docs/architecture/precise-types-design.md, rule C4)"
            )
    return problems


# --------------------------------------------------------------------------- changelog


_SPAN = re.compile(r"`([^`]+)`")
_QUALIFIED = re.compile(r"^((?:testprotocols|testoperations)(?:\.[A-Za-z_]\w*)*):(.*)$", re.S)
_CHAIN = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*")
_IDENT = re.compile(r"[A-Za-z_]\w*")


@dataclass(frozen=True)
class Names:
    """What a changelog entry or register row names."""

    modules: frozenset[str]
    tokens: frozenset[str]


def names_in(text: str) -> Names:
    modules: set[str] = set()
    tokens: set[str] = set()
    for raw in _SPAN.findall(text.replace("\\|", "|")):
        span = raw.strip()
        q = _QUALIFIED.match(span)
        if q is not None:
            modules.add(q.group(1))
            span = q.group(2)
        chain = _CHAIN.match(span)
        if chain is not None:
            parts = chain.group(0).split(".")
            tokens.update(parts)
            tokens.update(".".join(parts[: i + 1]) for i in range(len(parts)))
        if "(" in span:
            tokens.update(_IDENT.findall(span[span.index("(") :]))
    return Names(frozenset(modules), frozenset(tokens))


def _owner_and_member(change: Change) -> tuple[str, str | None]:
    _, _, qual = change.path.partition(":")
    return qual, change.member


def names_change(names: Names, change: Change, aliases: set[str], *, need_module: bool) -> bool:
    """Whether *names* names *change*'s symbol (and member, field or parameter)."""
    if need_module and not (names.modules & aliases):
        return False
    owner, member = _owner_and_member(change)
    if owner not in names.tokens:
        return False
    if member is None:
        return True
    if member in names.tokens or f"{owner}.{member}" in names.tokens:
        return True
    return change.param is not None and change.param in names.tokens


def _register_rows(head_root: Path) -> list[tuple[str, Names]]:
    path = head_root / DEPRECATIONS
    if not path.is_file():
        return []
    return [(r.package, names_in(r.item)) for r in register_rows(path.read_text("utf-8"))]


def check_changelog(
    changes: list[Change], changelog_text: str, head: Surface, changelog_path: str
) -> list[str]:
    """One line per breaking change no ``[Unreleased]`` entry names under a needed subsection.

    Marks each covered change's ``covered_by``.
    """
    entries, heading = unreleased(changelog_text)
    if heading is None:
        return [f"{changelog_path}: no `## [Unreleased]` heading"]
    parsed = [(e, names_in(e.subject)) for e in entries]
    rows = _register_rows(head.root)
    problems: list[str] = []
    for change in changes:
        if not change.needs:
            continue
        sym = head.symbols.get(_defining_key(change, head))
        aliases = set(sym.paths) if sym is not None else {change.path.partition(":")[0]}
        needs = set(change.needs)
        whole = replace(change, member=None, param=None)
        class_wide = False
        if sym is not None and _deprecated_with_row(sym, change, rows, aliases):
            needs.add(DEPRECATED)
            class_wide = sym.deprecated
        for entry, names in parsed:
            if entry.package != change.package or entry.subsection not in needs:
                continue
            if names_change(names, change, aliases, need_module=True) or (
                class_wide
                and entry.subsection == DEPRECATED
                and names_change(names, whole, aliases, need_module=True)
            ):
                change.covered_by = f"{changelog_path}:{entry.line}"
                break
        else:
            problems.append(
                f"{change.summary()} — not named in {changelog_path} [Unreleased] under "
                f"### {change.package} #### "
                + " | ".join(s for s in (BREAKING, CONSUMER, DEPRECATED, CHANGED) if s in needs)
            )
    return problems


def _defining_key(change: Change, head: Surface) -> str:
    module, _, qual = change.path.partition(":")
    for sym in head.by_name(qual):
        if module in sym.paths:
            return sym.key
    return change.path


def _deprecated_with_row(
    sym: Symbol, change: Change, rows: list[tuple[str, Names]], aliases: set[str]
) -> bool:
    """Whether the change's member (or class) carries ``@deprecated`` and has a register row."""
    if sym.deprecated:
        change = replace(change, member=None, param=None)
    elif not (
        change.member is not None
        and change.member in sym.members
        and sym.members[change.member].deprecated
    ):
        return False
    return any(
        package == change.package and names_change(names, change, aliases, need_module=False)
        for package, names in rows
    )


# --------------------------------------------------------------------------- output


def to_markdown(changes: Sequence[Change], problems: Iterable[str]) -> str:
    lines = ["# Contract surface changes", ""]
    if not changes:
        lines.append("No change to the contract surface.")
    for change in changes:
        box = "x" if (not change.needs or change.covered_by) else " "
        tail = ""
        if change.needs:
            tail = (
                f" — covered by {change.covered_by}"
                if change.covered_by
                else " — needs " + " | ".join(change.needs)
            )
        lines.append(f"- [{box}] `{change.summary()}`{tail}")
    problem_list = list(problems)
    if problem_list:
        lines += ["", "## Failures", ""]
        lines += [f"- {p}" for p in problem_list]
    return "\n".join(lines) + "\n"


def to_json(changes: Sequence[Change], problems: Iterable[str]) -> str:
    rows = [asdict(c) | {"symbol": c.symbol} for c in changes]
    return json.dumps({"changes": rows, "failures": list(problems)}, indent=2) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--base", type=Path, required=True, help="the base tree")
    parser.add_argument("--head", type=Path, required=True, help="the head tree")
    parser.add_argument("--format", choices=("json", "md"), default="md")
    parser.add_argument("--check-changelog", type=Path, metavar="CHANGELOG.md")
    parser.add_argument("--check-enum-params", action="store_true")
    args = parser.parse_args(argv)
    base = read_surface(args.base)
    head = read_surface(args.head)
    changes = diff(base, head)
    problems: list[str] = []
    if args.check_changelog is not None:
        text = args.check_changelog.read_text(encoding="utf-8")
        problems += check_changelog(changes, text, head, str(args.check_changelog))
    if args.check_enum_params:
        problems += enum_param_problems(base, head)
    render = to_json if args.format == "json" else to_markdown
    sys.stdout.write(render(changes, problems))
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
