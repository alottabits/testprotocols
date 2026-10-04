# Design: precise types across the released contracts

| Field   | Value                                                                 |
| ------- | --------------------------------------------------------------------- |
| Status  | In progress                                                           |
| Author  | rjvisser                                                              |
| Date    | 2026-10-04                                                            |
| Related | `docs/proposals/README.md` (question 9, precise types), `CONTRIBUTING.md` (Versioning), `testprotocols.deprecation`, `testprotocols.models._sync`, `packages/testprotocols/tests/test_typing_ratchet.py` |

## Purpose

The proposal review asks every added or changed member to be typed precisely
(question 9). Members released before that question existed are not all typed
that way: closed vocabularies are plain `str`, grammars are text, absent values
are `""` or `0`, and some records are `Any`. This document records how the
released contracts are brought to precise types without breaking a caller or a
driver in one step: every retype is a deprecation (widen, then narrow), and the
shapes below are the only ones used.

## The precise-types rule

- A value from a closed set (a mode, state, action, direction, protocol) is an
  `Enum` (`StrEnum` or `IntEnum`), never a free-form `str` and never a
  `Literal`. A set a registry closes is a pure enum.
- A vocabulary a device may legitimately extend is an enum with an `OTHER`
  member and a companion raw-text field (`<field>_raw: str | None`) holding the
  device's own word, so nothing is lost or guessed (shape 3o).
- `str` stays only for open values: interface, object, route, server, zone,
  file, BSS and user names, and similar.
- A grammar held as text (port lists, `(kind, value)` pairs) becomes a typed
  record; the text form stays readable during the deprecation period.
- Records are dataclasses, never a `dict` or a bare `tuple`; a new record is
  `@dataclass(frozen=True)` unless it extends a model that is already mutable.
- An absent value is `X | None`, never an empty-string or zero sentinel.
- No explicit `Any` in a signature or field. `tests/test_typing_ratchet.py`
  caps the explicit-`Any` count per package; every retype lowers the ceiling and
  none raises it. When the count reaches zero the ratchet is replaced by mypy's
  `disallow_any_explicit`.

## Deprecation shapes

Each retype names one of these shapes. The building blocks are reused, never
copied: `testprotocols.deprecation` (`coerce_enum`, `warn_renamed`,
`renamed_attribute`, `MODEL_FRAMES`) and `testprotocols.models._sync`.

- **Shape 1: a released `str` parameter becomes an enum.** The parameter is
  annotated `E | str`. A driver or operation coerces it once, at its boundary
  and before any device I/O, with `coerce_enum(E, value, what=…)`: a member
  passes, a plain string naming a member warns (`DeprecationWarning`) and
  converts, any other string raises `ValueError` listing the legal values.
- **Shape 1i: a released `str` parameter that is really a number becomes
  `int`.** The parameter is annotated `int | str`; `coerce_int` returns the
  int and warns on a numeric string, and a non-numeric string raises
  `ValueError`.
- **Shape 3: a released model field becomes an enum.** The field is annotated
  `E | str` and the model coerces it in `__setattr__` (a mutable model) or
  `__post_init__` (a frozen one), with `skip_file_prefixes=MODEL_FRAMES` so the
  warning points at the caller's construction or assignment site. A reader
  always holds the member.
- **Shape 3o: an extensible enum field.** The field is typed `E`; an unknown
  device word becomes `E.OTHER` and the raw word goes in
  `<field>_raw: str | None`. A plain string naming a member converts with a
  warning. A string that names no member becomes `OTHER` plus the raw word,
  with no error and no warning, because the set is open by contract.
- **Shape 4(ii): a released field holding a grammar becomes structured.** A
  new typed field is added beside the text field and the two are kept in
  agreement through `_sync` (below).
- **Shape 4p: a free-string tool parameter becomes typed keyword
  parameters.** The typed keyword-only parameters are added; the old string
  parameter stays, documented as deprecated, and warns when non-empty; passing
  both raises `ValueError`. No parameter changes position.
- **Shape 5: a tuple, dict or `Any` record return becomes a dataclass.** A new
  member name returns the dataclass. The old name is documented "Deprecated
  name of …" and an implementer delegates to the new one after
  `warn_renamed`. `testoperations` callers move to the new name through a
  typed fallback accessor, new name first, then the old.
- **Shape 6: announced only.** A return narrowing to an enum, and a `""`,
  `0` or `"any"` placeholder becoming `None`, get a docstring sentence and a
  *Deprecated* changelog entry. The type changes at the removal step.

A narrowing that takes effect at once (a value that was never meaningful now
raises) is recorded under *Changed* in the changelog.

## Synced fields: the side that changed wins

A shape 4(ii) retype keeps a deprecated text field (or several fields that
together spell one value, such as a `(kind, value)` pair) and its typed
successor in agreement. `testprotocols.models._sync` holds the rule once;
a model declares one `SyncedField` (one text field) or `SyncedFields` (several)
per pair and calls `settle` from `__post_init__` and `assign` from
`__setattr__`.

- **At construction**, a typed value fills the text; the text alone warns and
  fills the typed value; both given and disagreeing raise `ValueError`.
- **Through `dataclasses.replace` and assignment, the side that changed
  wins.** Changing the typed field rewrites the text silently; changing the
  text re-parses it into the typed field and warns. Both changed and
  disagreeing raise `ValueError`.
- **Parse before warn.** Malformed text raises `ValueError` without warning
  and changes nothing.
- **Type errors.** A text field assigned a non-text value, or an enum-typed
  text field assigned a value of another type, raises `TypeError`; a plain
  string for an enum-typed text field converts through `coerce_enum`.
- **Provenance last.** A hidden provenance field (`repr=False`,
  `compare=False`) records the agreed text of every pair; `replace` copies it,
  which is how a changed side is told from an unchanged one. It must be the
  model's last field, because the generated `__init__` assigns in field order;
  `settle` raises `TypeError` otherwise.
- Text is kept in its canonical form, so two records that agree compare equal
  whichever side built them.
