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
  caps the explicit-`Any` count per package; a retype may lower the ceiling and
  never raises it. When the count reaches zero the ratchet is replaced by mypy's
  `disallow_any_explicit`.

## Deprecation shapes

Each retype names one of these shapes. The building blocks are reused, never
copied: `testprotocols.deprecation` (`coerce_enum`, `coerce_int`,
`coerce_open_enum`, `warn_renamed`, `renamed_attribute`, `MODEL_FRAMES`),
`testprotocols.models._sync` and, for shape 3o, `testprotocols.models._open_enum`.

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
- **Shape 3o: an extensible enum field.** The field is annotated `E | str` (as
  shape 3, so a caller may still pass a plain string) and always holds a member
  after construction; `E` has a catch-all `OTHER`, and the device's own word is
  held in `<field>_raw: str | None`, only while the field is `OTHER`. A plain
  string naming a member converts with a warning (an exact match). Any other
  string, the empty one included, becomes `OTHER` plus the raw word, kept
  verbatim, with no error and no warning, because the set is open by contract.
  The pair is an `OpenEnumPair` (`models/_open_enum.py`), a `_sync` pair with
  the same hidden provenance field, so it agrees after construction,
  `replace` and assignment, and **the side that changed wins**: a member clears
  the raw word, an unknown string sets it, changing only the raw word keeps the
  field. A raw word beside a named member, or one that disagrees with the unknown
  word the field was given, raises `ValueError` and changes nothing. A frozen
  record calls `settle` from `__post_init__` alone; a mutable one adds `assign`
  in `__setattr__`. `coerce_open_enum` is the function-level form, for a driver
  boundary: it returns `(member, raw)`.
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
  typed fallback accessor, new name first, then the old; the accessor module
  (`testoperations/_renamed.py`) arrives with the first shape 5 retype.
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

## Retypes

Each retype that has landed, with its shape. A capability's own design document,
where one exists, also records its retype.

- **Firewall, NAT and conntrack vocabularies** (shapes 1, 3, 3o and 6). Five
  enums in `testprotocols.models`: `Chain` (`INPUT`, `OUTPUT`, `FORWARD`),
  `FirewallRuleAction` (`allow`, `deny`, `reject`, `log`), `NatMode` (`snat`,
  `dnat`, `1to1`), `PortMappingProtocol` (`tcp`, `udp`, `tcp-udp`) and
  `ConnState`. A rule's, NAT rule's and connection's transport is the existing
  `RuleProtocol`; a chain default policy is `DefaultAction`. The `chain`,
  `policy`, `mode`, `protocol` and `state` parameters of `PacketFilter`, `Nat`
  and `Conntrack` are `E | str` and a driver coerces once at each member
  (shape 1). The four closed vocabularies on `FirewallRule`, `NatRule`,
  `PortMapping` and `Connection` are shape 3: the records are mutable, so the
  coercion is a `__setattr__`, and a plain string warns while an unknown one
  raises `ValueError`. `ConnState` is open (shape 3o): the released contract
  listed nine TCP states, `UNREPLIED` and `ASSURED`, "or driver-specific
  values", so it has those members plus `OTHER`. Its values are exactly the
  released upper-case words (`"ESTABLISHED"`), so `conn.state == "ESTABLISHED"`
  still holds; every enum of this retype equals its released strings. The device's
  own word is in `Connection.state_raw` while the state is `OTHER`. An unknown
  word never raises and never warns; a named plain string warns. Edge words: the
  match is exact, so `"established"` and `"other"` are unknown words (`OTHER` plus
  that raw word), `""` is an unknown word kept as `""`, and `"OTHER"` names the
  member (a warning, no raw word). The pair follows the shape 3o rule above:
  the side that changed wins under `replace` and assignment; a raw word with a
  named state raises `ValueError`. A `state` filter with an unknown word matches flows whose
  `state_raw` equals it. A conntrack `protocol` filter of `any` is refused: a
  flow has one transport, and so is `Connection.protocol`, which raises
  `ValueError` for `RuleProtocol.ANY`. `get_default_policy` keeps returning `str`
  (shape 6, announced only).
- **Firewall and NAT ports and counters** (shapes 4(ii), 5 and 6). `FirewallRule`
  gains `dst_ports` and `NatRule` gains `dst_ports` and `translated_ports`, each a
  `tuple[PortRange, ...]` synced with its deprecated text field through `_sync`.
  A record has one provenance field (`_ports_seen`, last), shared by all its pairs,
  and the same `__setattr__` also applies the enum coercion of the vocabularies
  retype. `FirewallRule.dst_port` now defaults to `"any"` (its released contract
  allowed `"any"`; the default lets a rule be built from `dst_ports` alone). The
  released `NatRule` contract used `""` for no port, so its pairs use `""` as the
  canonical empty text (`"any"` is accepted and reads back `""`), while
  `FirewallRule` keeps `"any"`. The `NatRule` cidr and translated-address `""`
  placeholders are announced only (shape 6). `RuleCounters(packets, bytes)`
  replaces the `(int, int)` tuple: the new members
  `PacketFilter.get_rule_counter_values` and `Nat.get_nat_rule_counter_values`
  are mandatory (breaking for driver authors), the old names deprecated (shape 5).
  `testoperations` does not call either old name.
- **SD-WAN models** (shapes 4(ii) and 6). `L3Rule` gains `src_ports` and
  `dst_ports`, `tuple[PortRange, ...]` synced with the deprecated `src_port` /
  `dst_port` text through `_sync`, one provenance field (`_ports_seen`) for both
  pairs, as on `FirewallRule`. `SecurityEvent` gains `timestamp: datetime | None`
  synced with the deprecated ISO-8601 `ts`. The codec is `datetime.fromisoformat`
  and `datetime.isoformat()`; a timezone-naive value stays naive and no zone is
  assumed. An ISO-8601 instant has several equal spellings (`Z` or `+00:00`, `T` or
  a space), and `isoformat()` writes one, so `isoformat()` does not round-trip a
  producer's text: the pair is a `SyncedField` with `keep_text=True`, which keeps a
  text that parses to the agreed value exactly as given (a typed value alone writes
  `isoformat()`). Two events with the same instant in two spellings therefore
  compare unequal on `ts`. `ts` gained a default (`""`, no time) so an event can
  be built from `timestamp` alone; the fields after it keep their released
  positions and take a required-argument placeholder that `__post_init__` refuses,
  so omitting one still raises `TypeError`. The `"any"` cidr placeholders of
  `L3Rule`, the `""` placeholders of `UplinkStatus` and `NetworkAttachment.segment`
  are announced only (shape 6).

## Effective now

Changes that take effect in this release for code written against the released
contract, whether or not it uses the deprecated spelling. Each task appends here;
the matching CHANGELOG entry sits under *Changed*.

- **Conntrack and coercion** (vocabularies task). `Connection.protocol` refuses
  `RuleProtocol.ANY` with `ValueError`, as the released docstring said. An unknown
  string on `FirewallRule`, `NatRule`, `PortMapping` or `Connection` (protocol, mode,
  action) raises `ValueError`; a `Connection.state` unknown word never raises: it
  becomes `ConnState.OTHER` plus `state_raw`. A conntrack `protocol` filter of `any`
  is refused. `NatRule.protocol` defaults to `RuleProtocol.ANY`.
- **Firewall and NAT ports** (ports task). `FirewallRule.dst_port` now defaults to
  `"any"`. `NatRule` port text reads `""` for no port (`"any"` is accepted and reads
  back `""`). Port text accepts only `"any"` (or `""` on `NatRule`), numbers, `a-b`
  ranges and comma lists with no trailing comma; colon or slash forms (`"80:90"`,
  `"tcp/80"`) and a trailing comma raise `ValueError`, so a driver that reads them
  back must convert them. A non-text port text or a non-`PortRange` item raises
  `TypeError`.
- **Static-only: unpacking a loose dict** (ports task; no runtime change). Unpacking
  a loosely typed dict, for example `FirewallRule(**dict[str, str])`, into a retyped
  released record fails type-checking, because the synced typed fields (`dst_ports`)
  and the hidden provenance field are keyword parameters and a type checker matches
  the dict's value type against each. The caller types the dict or passes the fields
  explicitly. The private `_ports_seen` also appears in `__init__` signatures and in
  static error text; it is not API.
- **SD-WAN models** (SD-WAN task). `L3Rule.src_port` / `dst_port` follow the
  `FirewallRule` port rule: only `"any"`, numbers, `a-b` ranges and comma lists are
  text that parses (`""`, `"http"`, `"80:90"` and a trailing comma raise
  `ValueError`; a non-text value raises `TypeError`), and text reads back
  canonical. `SecurityEvent.ts` raises `ValueError` for text `datetime.fromisoformat`
  does not parse (released: any string was accepted) and `TypeError` for a
  non-text value. Static only: unpacking a loosely typed dict into `L3Rule` or
  `SecurityEvent` fails type-checking, as for `FirewallRule` (the keyword
  parameters `src_ports`, `dst_ports`, `timestamp` and the private `_ports_seen`
  and `_ts_seen`).

## Pending narrow steps (announced, not yet taken)

Each lands in a later release with its own breaking changelog entry:

- Enum-only parameters and fields: the firewall, NAT and conntrack parameters
  and fields (`Chain`, `DefaultAction`, `NatMode`, `RuleProtocol`,
  `FirewallRuleAction`, `PortMappingProtocol`, `ConnState`) narrow from
  `E | str` to `E`; `get_default_policy` narrows to `DefaultAction`.
- The `NatRule` cidr and translated-address `""` placeholders become `str | None`;
  the port text fields and the old counter names are removed.
- The `L3Rule` cidr `"any"` placeholders, the `UplinkStatus` address `""`
  placeholders and `NetworkAttachment.segment` `""` become `str | None`; the
  `L3Rule` port text fields and `SecurityEvent.ts` are removed.
