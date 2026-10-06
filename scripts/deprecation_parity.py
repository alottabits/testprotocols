"""Every copy of a deprecation fact agrees: marker, docstring and register row.

A deprecation in this repository is written in up to four places
(``docs/architecture/precise-types-design.md``, rule C2 and "Deprecations"): the
``@deprecated`` marker, the docstring's deprecation paragraph, the row of
``packages/testprotocols/DEPRECATIONS.md`` and the *Deprecated* changelog entry. The
register and the changelog are matched by ``changelog_entries.register_problems`` (run by
``hygiene``); this module checks the rest, from the source by :mod:`ast` (nothing is
imported):

- every ``@deprecated`` site in ``packages/*/src`` passes a sentence equal to its
  docstring's deprecation paragraph (the paragraph that starts with ``Deprecated``),
  read with whitespace collapsed and Sphinx roles (``:meth:``), ``~`` and backticks
  dropped;
- a register row names every ``@deprecated`` site (a ``member`` row its
  ``Class.member``, a ``class`` row its class);
- every ``next release`` row names a symbol of its package's source: in
  ``testprotocols`` a ``member`` or ``class`` row names one that carries ``@deprecated``,
  except a row about a member's return type (its item says ``return``), which no marker
  can state; every other row (a parameter, field or attribute, which cannot carry the
  marker; a return type; a ``testoperations`` form, which warns at run time instead,
  rule C6) names, first, a symbol whose docstring states it: it says ``deprecated``,
  ``announced`` (design, "Shape 6: announced only") or that the form narrows (``narrows
  to``, ``narrowing``), the register's own words for a retype. An enum or alias a row
  names is its replacement type, not its subject.

Usage: ``python scripts/deprecation_parity.py [ROOT]`` (default: the current directory).
Each problem is one line naming the file, the line and the rule; exit status 1 when there
is one.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from changelog_entries import DEPRECATIONS, NEXT_RELEASE, Row, register_rows
from contract_surface import Member, Surface, Symbol, read_surface

_RULE_MARKER = "(precise-types-design.md, rule C2)"
_RULE_REGISTER = "(DEPRECATIONS.md, Adding a row)"
_ROLE = re.compile(r":[a-z]+:(?=`)")
_SPAN = re.compile(r"`([^`]+)`")
_QUALIFIED = re.compile(r"^(?:testprotocols|testoperations)(?:\.[A-Za-z_]\w*)*:")
_CHAIN = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*")
_STATED = re.compile(r"deprecat|announced|narrows? to|narrowing", re.IGNORECASE)
_RETURN = re.compile(r"\breturns?\b")


def normalise(text: str) -> str:
    """*text* with Sphinx roles, ``~`` and backticks dropped and whitespace collapsed."""
    text = _ROLE.sub("", text).replace("`", "").replace("~", "")
    return " ".join(text.split())


def deprecation_paragraph(docstring: str) -> str | None:
    """The docstring paragraph that starts with ``Deprecated``, or ``None``."""
    for paragraph in re.split(r"\n\s*\n", docstring):
        if paragraph.strip().startswith("Deprecated"):
            return paragraph
    return None


@dataclass(frozen=True)
class Site:
    """One ``@deprecated`` class or member."""

    symbol: Symbol
    member: Member | None

    @property
    def name(self) -> str:
        return self.symbol.name if self.member is None else f"{self.symbol.name}.{self.member.name}"

    @property
    def line(self) -> int:
        return self.symbol.line if self.member is None else self.member.line

    @property
    def marker(self) -> str | None:
        return self.symbol.marker if self.member is None else self.member.marker

    @property
    def docstring(self) -> str:
        return self.symbol.docstring if self.member is None else self.member.docstring


def sites(surface: Surface) -> list[Site]:
    found: list[Site] = []
    for sym in surface.symbols.values():
        if sym.deprecated:
            found.append(Site(sym, None))
        found += [Site(sym, m) for m in sym.members.values() if m.deprecated]
        if sym.function is not None and sym.function.deprecated and not sym.deprecated:
            found.append(Site(sym, None))
    return sorted(found, key=lambda s: (s.symbol.file, s.line))


def _chains(item: str) -> list[list[str]]:
    out: list[list[str]] = []
    for span in _SPAN.findall(item.replace("\\|", "|")):
        chain = _CHAIN.match(_QUALIFIED.sub("", span.strip()))
        if chain is not None:
            out.append(chain.group(0).split("."))
    return out


def _row_names_site(row: Row, site: Site) -> bool:
    if row.package != site.symbol.package:
        return False
    for chain in _chains(row.item):
        if site.member is None and row.kind == "class" and chain == [site.symbol.name]:
            return True
        if site.member is not None and chain[:2] == [site.symbol.name, site.member.name]:
            return True
    return False


def _targets(row: Row, surface: Surface) -> list[tuple[Symbol, Member | None]]:
    """The symbols (and members) a row's code spans name, in its package."""
    out: list[tuple[Symbol, Member | None]] = []
    for chain in _chains(row.item):
        for sym in surface.by_name(chain[0]):
            if sym.package != row.package or sym.kind in {"enum", "alias"}:
                continue  # an enum or alias in a row is the replacement type
            member = sym.members.get(chain[1]) if len(chain) > 1 else None
            if (sym, member) not in out:
                out.append((sym, member))
    return out


def _stated(sym: Symbol, member: Member | None) -> bool:
    if member is not None:
        return bool(_STATED.search(member.docstring))
    texts = [sym.docstring, *(m.docstring for m in sym.members.values())]
    return any(_STATED.search(t) for t in texts)


def problems(root: Path) -> list[str]:
    surface = read_surface(root)
    register_path = root / DEPRECATIONS
    rows = register_rows(register_path.read_text("utf-8")) if register_path.is_file() else []
    out: list[str] = []
    for site in sites(surface):
        where = f"{site.symbol.file}:{site.line}: `{site.name}`"
        paragraph = deprecation_paragraph(site.docstring)
        if site.marker is None:
            out.append(f"{where} @deprecated has no literal sentence {_RULE_MARKER}")
        elif paragraph is None:
            out.append(
                f"{where} docstring has no paragraph starting `Deprecated` to match its "
                f"@deprecated sentence {_RULE_MARKER}"
            )
        elif normalise(paragraph) != normalise(site.marker):
            out.append(
                f"{where} @deprecated sentence {normalise(site.marker)!r} differs from the "
                f"docstring's {normalise(paragraph)!r} {_RULE_MARKER}"
            )
        if not any(_row_names_site(row, site) for row in rows):
            out.append(
                f"{where} @deprecated but no row of {DEPRECATIONS} names it {_RULE_REGISTER}"
            )
    for row in rows:
        if row.deprecated_in != NEXT_RELEASE:
            continue
        where = f"{DEPRECATIONS}:{row.line}: {row.kind} row"
        targets = _targets(row, surface)
        if not targets:
            out.append(f"{where} names no symbol of `{row.package}` {_RULE_REGISTER}")
            continue
        marked_kind = row.package == "testprotocols" and row.kind in {"member", "class"}
        if marked_kind and not _RETURN.search(row.item):
            sym, member = targets[0]
            marked = sym.deprecated if member is None else member.deprecated
            if not marked:
                name = sym.name if member is None else f"{sym.name}.{member.name}"
                out.append(f"{where} names `{name}`, which carries no @deprecated {_RULE_MARKER}")
            continue
        sym, member = targets[0]
        if not _stated(sym, member):
            name = sym.name if member is None else f"{sym.name}.{member.name}"
            out.append(
                f"{where} names `{name}`, whose docstring does not state the deprecation "
                f"(no `deprecated`, `announced` or `narrows to`) {_RULE_MARKER}"
            )
    return out


def main(argv: list[str]) -> int:
    root = Path(argv[0]) if argv else Path()
    found = problems(root)
    for problem in found:
        print(problem)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
