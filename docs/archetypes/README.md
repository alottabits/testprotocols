# Introducing a device archetype

A device archetype is the vendor-neutral shape tests are written against for
one device class. Introducing one is not a proposal for a symbol: it is a
survey of how the vendor offerings in a device category publish their
operations, carried out to arrive at a method set that is neither too narrow
(one vendor's model in neutral clothing) nor too wide (members no family can
satisfy). This page is the canonical statement of how that is done here. The
reviewer's working method is not published (CONTRIBUTING.md, "How this
differs from a typical GitHub project").

A consumer **requests** an archetype; a maintainer runs the work. The design
still passes agent review before it merges.

## The stages

One document, `docs/architecture/<slug>-protocol-design.md`, grows through
the stages. Its **Status** names the stage: `chartered` → `accepted for
verification` → `verified`.

| # | Stage | Where | Reviewer | Exit |
| --- | --- | --- | --- | --- |
| 0 | Request | issue from the `archetype-request` template, or a private request held by the maintainers | maintainer | a charter is opened, or the request is declined with the reason |
| 1 | Charter | PR `charter: <slug>`, merged to `main`; adds the document with Status `chartered` and only its Charter section | archetype reviewer, charter questions | merge ratifies the class definition and the reviewed-family list; it commits scope only, no contract |
| 2 | Exploration | branch `archetype/<slug>`, no PR | none | the maintainer opens the design PR |
| 3 | Design | PR `archetype: <slug>`, the document only | archetype reviewer, design questions; three rounds | verdict not `request changes`, every manifest row has an Outcome, Status `accepted for verification`; **not merged** |
| 4 | Verification | the same PR gains the core code, tests and changelog entries; a reference driver per ratified family is written in the private corpus | code reviewer and archetype reviewer, verification questions | `conformance` green; every finding folded back into the document in place and recorded in its review record |
| 5 | Land | merge with Status `verified`; then a `release:` | release reviewer | tag, publish |

Nothing but the charter reaches `main` before verification: an accepted
design on `main` is a recorded decision every later review reads.

A tier below the majority, left `tier-staged`, becomes a GAPS pointer at merge. When its trigger
fires (a second consumer or a second trigger family), it arrives through an
ordinary `proposal:` citing the design path and row id, and its reference
drivers arrive with the implementing `feat:` PR.

A charter that cannot be agreed after three rounds is closed, not merged. A
status refresh after an approve verdict (CONTRIBUTING.md, "A PR's life",
step 4) is not a round at any stage. A
design that fails verification is reshaped on its branch, or its PR is closed
with the reason recorded; the charter stays on `main` with a closing note in
its review record.

## The request

Open an issue from the `archetype-request` template. The consumer's tests may
live in a private repository, so the request states their **intents in
neutral domain terms**, never their code:

- **Device class**, in neutral words, never a product line.
- **Trigger families**, preferably at public version lines. Example models
  from a vendor's public catalog are welcome as illustrations of the class.
  **No inventory**: no counts, no sites, no per-box firmware list. The charter
  turns examples into version lines.
- **Use case ids** (`UC-nnn`), optional.
- **Test intents**, one row per test the consumer needs to write:

  | Intent | Operations exercised | Nearest archetype, and why it fails |
  | --- | --- | --- |
  | one sentence | the operations, neutrally named | the archetype tried, and the over- or under-specification that rules it out |

The neutrality rule of `docs/proposals/README.md` applies to the issue.

**A private request.** When the test intents come from material the consumer
cannot make public, a maintainer records the same fields in the maintainers'
private reference corpus instead of an issue. The charter then lists only the
operations it needs and says that the demand evidence is held privately; the
archetype reviewer reads the private request and answers the demand question
by intent id and by the charter's operations, never by quoting it. A review
that quotes a private request is withheld, like one that quotes the corpus.

## The design document

The document uses this skeleton; `hygiene` reads the Status row, `## 1.
Charter` and `## 12. Landing manifest`.

```markdown
# Design: vendor-neutral **<class>** archetype

| Field | Value |
| --- | --- |
| Status | chartered |
| Author | <handle> |
| Date | YYYY-MM-DD |

## 1. Charter
## 2. Cross-family matrix
## 3. Decision
## 4. The archetype
## 5. Reuse vs. net-new
## 6. Modelling decisions
## 7. Levels
## 8. Driver-facing neutrality notes
## 9. Verification
## 10. Sources
## 11. Open questions
## 12. Landing manifest
## Review record
```

1. **Charter** — the class defined by the operations its management planes
   publish, never by transport, management mode or vendor; the boundary with
   each registered archetype (where it is over- or under-specified for this
   class, and why no tier or extension of it meets the need); the trigger
   families at public version lines; the reviewed-family list, each family
   with a one-line reason in or out. At stage 1 this section is the whole
   document, with the review record.
2. **Cross-family matrix** — operation × family, every cell ✓ / ◐ / ✗ with a
   source; denominators counted against the ratified list; every ◐ listed as
   a verification item.
3. **Decision.**
4. **The archetype** — core plus optional tiers, each tier with its trigger.
5. **Reuse vs. net-new** — every operation the design adds, placed on the
   placement ladder (below): its rung, and for every item above rung 2 why
   no cheaper rung fits; a shared-with table per sibling archetype.
6. **Modelling decisions** — each stated as the decision and the condition
   that would overturn it.
7. **Levels** — sea-level and white-box per `packages/testprotocols/LEVELS.md`.
8. **Driver-facing neutrality notes.**
9. **Verification** — the reference families, and the cells expected to be
   unsupported.
10. **Sources.**
11. **Open questions.**
12. **Landing manifest** — below.

**Review record** — the only place for the design's history; every other
section states decisions only. It holds the charter review, both design
rounds, every verification finding and its fold-back, and the corpus commit
the verification ran against.

Vendor and product names appear only in the matrix, the sources and the
driver-facing notes.

### The landing manifest

| Id | Kind | Symbol | Mechanism | Placement | Breaking | Outcome |
| --- | --- | --- | --- | --- | --- |
| M1 | new protocol / new field / new archetype / new tier / rename / SPLITS entry / GAPS entry / LEVELS entry | `module:Symbol` | a ladder rung, or `archetype` / `record` | `core`, `tier — <tier name>` or `tier-staged — <trigger>` | yes / no | accepted / accepted with conditions / declined, date |

Every symbol change the body mentions has a row. `core` and `tier` rows are
implemented on the `archetype:` PR and get changelog entries citing `<design path> M<n>`.
`tier-staged` rows get a pointer in `packages/testprotocols/GAPS.md` naming the
document before the PR merges at `verified`. A later `feat:` PR cites a row
the way it cites a proposal's `P<n>`.

## The placement ladder

Every operation a design adds is placed on the placement ladder of
`docs/proposals/README.md` ("The placement ladder"): the lowest rung that
genuinely fits, with the reason no lower rung does for every item above
rung 2. The manifest records each row's rung in its Mechanism column, with
`archetype` for an archetype or tier row and `record` for a tracking-file
entry; the Breaking column is `yes` exactly for `extend` and `remove` rows. `hygiene`
checks both.

## The evidence bar

For an archetype **core**, a ratified reviewed-family list plus the sourced
matrix plus the reference corpus substitutes for a second consumer. A core
member is supported on every trigger family and on a majority of the ratified
list; anything else is a tier or a documented per-method unsupported case. A
**tier** is built on the archetype PR when its members are supported on a
majority of the ratified list: its matrix evidence stands in for the second
consumer, as the core's does. Its manifest rows carry Placement
`tier — <tier name>` and are implemented and tested like core rows, and a
family that lacks a member raises the documented unsupported case. A tier
below the majority still waits for a second consumer or a second trigger
family and stays `tier-staged` (amended 2026-10-19; until then every tier
waited).

## The reference corpus and the `conformance` check

The maintainers keep a **private** reference corpus: one reference driver per
ratified family, written against the family's published documentation in the
shape a real driver takes (a `VitroDevice` with the family's transports as
routes and one implementation per capability). Every method carries out the
family's published operation and cites its source; an unsupported cell raises
`NotSupportedError` with the source of the absence. The drivers validate the
**shape** — that the proposed methods map onto each family's way of working —
not driver behaviour, and they are never run against a device.

Four properties every reference driver shows, because a real driver needs
them and a design that makes them impossible is wrong:

- **The plugin driver shape.** One route holder per transport whose capability
  slots are annotated with the protocol types; every capability aliased from
  the typed route holder onto the driver explicitly, one at a time; static
  conformance checked by the type checker on the concrete driver class, not
  only by `isinstance`.
- **Write outcome.** A write promises its acknowledgement, not the
  device's resulting state: the call returns normally only when the
  family acknowledged the write, and raises a rejection error when the
  device refused it, from the device's own error output or status. Whether
  the device then holds the state asked for is shown by the contract's
  paired read (design question 8) and confirmed by the test, directly or
  through a `testoperations` operation it opts into — never by a read-back
  inside the driver. The driver cannot tell per call whether an
  acknowledgement was silent about a partial failure; that is a property
  of the family, so a read-back "where the acknowledgement is unreliable"
  is a read-back on every write of that family, paid by every caller,
  needing family-specific equivalence code for what the device
  normalises, and hiding device behaviour a test may want to observe. The
  test, by contrast, verifies a write only where its own assertion would
  not reveal the failure. What the device normalises on a write
  (ordering, filled defaults, a mode it forces) is stated in the
  contract's docstring, as the management-frame-protection rule is, so
  the test author compares with that knowledge. A removal promises the
  same: the acknowledgement of the delete, not the absence. A rejection
  partway through a multi-step write raises naming the step, and the
  driver writes nothing on the failure path: putting the as-found state
  back would make a non-transactional family look transactional, with a
  second multi-step write that can itself fail. The state after a
  rejection is the as-found state where the family commits atomically,
  otherwise the steps applied before the rejection; the driver documents
  which, and a test that continues after a rejection reads it. A lever
  names the observation that confirms it. Where the family applies the change
  to the device asynchronously (a controller or dashboard), the
  acknowledgement is the controller's, and the device-side effect is a
  `testoperations` wait, never a wait inside the driver. A write the
  contract gives no way to show cannot be confirmed by any test — hence
  design question 8.
- **Acknowledged calls.** No call is one-shot. Every call — write, read and
  lever — checks the device's immediate response before using its result.
  The session classifies every response once, per family (error output, a
  commit or check failure, an HTTP status, an error field in a successful
  body), and raises a rejection error, so a test can tell "the device
  refused" from "the device accepted"; this classification is the whole
  of the driver's duty on a write. Where the family publishes a
  positive acknowledgement (a commit confirmation, a created object's id, a
  job id, a status field, a confirmation prompt), the driver requires it and
  fails when it is missing; silence counts as success only where the
  vendor documents a silent success, and the driver cites that source. A
  read whose output does not parse fails; it never returns an empty
  result. A rejection partway through a multi-step write raises naming
  the step and writes nothing more.
- **Precise types.** Vendor responses are parsed into typed records at the
  session boundary; `Any` appears only where a third-party signature forces
  it and is narrowed at once; a closed set the driver compares on is an
  `Enum` or `Literal`; every type-checker suppression names its error code.
  The corpus runs mypy and pyright in strict mode.

The corpus is kept current with every archetype that went through this track:

- a change that **extends** such an archetype is promoted only when enough
  families can implement it (the core threshold above), and a maintainer adds
  it to every reference driver before the change merges;
- a change that **narrows** it shows which families no longer satisfy it.

A `conformance` status reports this on every PR that changes package source,
in public terms only: the public symbol and the number of families, never
the corpus content. A pull request from a fork gets `conformance` when a
maintainer runs `/review`. CONTRIBUTING.md lists the required checks. The
review record of a verified design names the corpus commit it was verified
against.

### Verifying a design that predates the track

An archetype that entered the contract before the track (Status
`Implemented`) is verified later the same way: reference drivers in the
corpus, merged to corpus `main`. A `docs:` PR then appends
`## Verification record (<date>)` to its design document and sets Status to
`Implemented; verified <date> against the reference corpus`. The record holds
the corpus `main` commit, the families with version lines, per-family counts
of members mapped, mapped with a stated gap and unsupported, the unsupported
cells by symbol and family, the findings for a later change proposal, and
the `GAPS.md` entries. Nothing else in the document changes, and no package
source; the `GAPS.md` entries the record lists may land in the same PR, as
entries of that file, since a record with its gaps is one decision. No
`conformance` check runs, since the PR carries no package source. Such a PR
takes the archetype reviewer, with the Verification record set below; its
question 5 reads the `GAPS.md` entries as part of the record.

## What the archetype reviewer asks

The reviewer answers one set per stage, in order, with the response format and
verdicts of `docs/proposals/README.md`.

**Charter** (`charter:` PR):

0. **Neutrality.** The proposal rule; trigger families as public version lines;
   example models only as public-catalog illustrations, never an inventory.
1. **Defined by published operations**, not by transport, management mode or
   vendor.
2. **Boundary with every existing archetype**, and whether a tier or extension
   of one would meet the need instead.
3. **Family list.** Every trigger family present; the major competitor
   families in, each with a reason in or out; large enough that the matrix
   denominators mean something.
4. **Demand.** The request's test intents map onto the charter's operations
   (a private request is read privately and not quoted).

**Design** (`archetype:` PR, document only):

0. **Neutrality.** Vendor names only in the evidence sections.
1. **Recorded decisions.** In line with `docs/architecture/`, SPLITS, LEVELS
   and the capability-only rule; reopening needs new evidence.
2. **Matrix soundness.** Every cell sourced; denominators against the ratified
   list; every ◐ a verification item.
3. **Placement ladder walked.** Every added operation sits on the cheapest
   rung that fits, and every item above rung 2 says why no cheaper rung does;
   no new capability holds a single verb of a concern that an existing or
   another new capability owns.
4. **Core vs. tiers.** Every core member meets the core threshold; everything
   else is `tier-staged` with its trigger, or a documented per-method
   unsupported case.
5. **Levels.** Sea-level vs. white-box per LEVELS.md; no vendor terms in method
   names at any level.
6. **No siblings.** No near-duplicate of an existing protocol, and no new
   name that reads as a variant of an unrelated existing one; every rename
   carries its deprecated form for the period.
7. **Manifest complete.** Every symbol change in the body has a row with its
   Mechanism, breaking flag and tracking-file entries.
8. **Every write verifiable.** Each member that changes device state has a
   read in the contract that shows the effect — `set_x` beside `get_x`, an
   `add` beside the list or get that finds it — so a driver can show the
   state after the write and fail when it did not take. A member with no
   state to show (a reload, a session reset, a lease renewal) is a
   **lever**, and the item names the observation that confirms it (the boot
   wait, the uptime, the session or lease state). A write-only member with
   neither is `not met`: no driver could ever show that it worked.
   The member promises its **acknowledgement**, not the device's resulting
   state: the call returns normally only when the family acknowledged the
   write, and raises a rejection error when the device refused it. Whether
   the device then holds the state asked for is what the paired read is
   for: the test confirms it, directly or through a `testoperations`
   operation, when its own assertion would not reveal the failure. A
   driver does not read the state back after a write
   (`docs/archetypes/README.md`, "Write outcome"). What the device
   normalises on a write (ordering, filled defaults, a mode it forces) is
   stated in the member's docstring, so the test compares with that
   knowledge; a normalisation the item leaves unstated is a condition.
   For each write a reviewed family realises in more than one device step
   (a list replace, delete-then-create, an ordered restore), the contract
   states its failure outcome: a write rejected at any step raises naming
   the step, and the driver writes nothing on the failure path. The state
   is then the as-found state where the family's own mechanism gives it
   (one commit of a candidate configuration, a transaction), and otherwise
   the steps applied before the rejection; which it is, is a per-family
   fact in the matrix or a `lossy:` line, never something the driver puts
   back. A multi-step write with no stated failure outcome, or one whose
   docstring promises the as-found state on every family, is `met with
   conditions`.
   A member whose effect a family applies to the device asynchronously (a
   controller that stores the change and pushes it later) promises the
   controller's acknowledgement; the item names the read that shows the
   device-side effect and the `testoperations` wait that observes it
   (question 11, Orchestration).
9. **Precise types.** Every member and model the design adds or changes is
   typed precisely, so that the structural check of a `Protocol` verifies
   something: no `Any` or `object` in a signature or field; a value from a
   closed set (a mode, state, action, direction or protocol) is an `Enum`,
   never a free-form `str`; `str` only for open values (names,
   descriptions, text the device returns verbatim); records are
   dataclasses, never a `dict` or a bare `tuple`; an absent value is
   `X | None` with its meaning stated, never an empty-string sentinel. An
   added or changed member typed imprecisely is `not met`. An existing
   member the design does not touch is noted, not blocking; retyping one is
   a rung-5 `deprecate` (widen, then narrow) with its manifest row.
10. **Proportionality.** As proposal question 10: each typing or contract
    change strengthens the static checks enough to justify its maintenance
    cost.
11. **Method grain.** As proposal question 11, over the ratified family
    list and the capabilities every archetype composing the design's
    capabilities holds. Atomicity is decided at three levels: the shape,
    the driver and the family (question 11, Atomic). A window the
    corpus shows is worked at the driver level first (verification item
    10) and reaches this item's Atomic verdict only when no documented
    mechanism closes it.

**Verification** (`archetype:` PR with package source):

1. **Coverage.** One reference driver per ratified family, pinned to the PR
   head; `conformance` green.
2. **Real mappings.** Every method carries out the family's published
   operation and fills the neutral model, citing its source; unsupported
   cells raise `NotSupportedError` with a source and nothing else. Citations
   are sampled against the published documentation.
3. **Matrix agreement.** ✓ is an implemented method, ✗ is `NotSupportedError`,
   ◐ is either, with a note naming what is partial; a mismatch names which
   side is wrong.
4. **Faithful mapping and precise types.** No vendor data carried in loosely
   typed fields; every lossy mapping recorded in the document; the package
   source meets design question 9 and the reference drivers have the
   precise types above, with mypy and pyright strict green.
5. **Driver shape.** Every reference driver has the plugin driver shape
   above, and the type checker verifies its conformance statically.
6. **Write outcome.** No state write reads the state back inside the
   driver, and no write puts anything back on a failure path; a
   device-reported failure fails the write naming the step; every lever
   names its confirming observation; every normalisation the family
   applies on a write is stated in the contract's docstring, or is a
   condition; and the matrix or a `lossy:` line says, per family, whether
   a rejected multi-step write leaves the as-found state or the steps
   before the rejection.
7. **Acknowledged calls.** Every call checks the device's immediate response
   as above: a rejection raises its own error, a published acknowledgement is
   required, a silent success cites its source, an unparsable read fails,
   and a rejection partway through a write raises naming the step and
   writes nothing more. The
   corpus's fakes emit each family's rejection output, so the negative path
   is tested.
8. **Findings folded back** into the matrix, body, manifest and review record.
9. **Method grain in the corpus.** Design question 11 applied to the
   reference implementations: an orchestration the drivers repeat family
   by family is noted with its breakdown; a combining operation that does
   not clean up on every exit, or does not test the abandoned path, is a
   condition.
10. **Atomicity and orthogonality in the corpus.** A driver whose write
    leaves a window inside the call is a condition where the family's
    documentation, or a comparable reference driver, shows a mechanism
    that avoids it (building a second generation and swapping the
    binding), otherwise a `lossy:` line with its source. A driver whose
    write disturbs another member's concern instead of refusing is a
    condition. A device resource the drivers find two members writing,
    which the design does not show as split or refused, is a condition
    folded back into the design. This item is worked before design item
    11's Atomic verdict: a window is a driver-level finding until the
    family's documentation and the comparable drivers show no mechanism
    that closes it, and only then a shape question.

**Verification record** (`docs:` PR on a design document):

1. **Corpus commit.** The record names a corpus `main` commit; the
   reviewer's checkout is that commit or a descendant of it.
2. **Counts.** Per family, mapped + mapped with a gap + unsupported = the
   archetype's member total; the totals agree with the corpus matrix.
3. **Unsupported cells sourced.** Every unsupported cell is a
   `NotSupportedError` with a source in the corpus (at least one checked per
   family, with one vendor page fetched).
4. **Matrix agreement.** The record's cells are checked against the design
   document's table: every disagreement has a correction line. Against the
   corpus matrix there is none.
5. **No shape change.** The diff touches only the appended section, the
   Status field and `GAPS.md` entries the record lists: no package source, no
   other document. The findings section and the entries propose and
   implement nothing.
6. **Neutrality.** Family names appear only in the record's version lines and
   cells; no customer trace; no corpus path or identifier.

The posted review cites only public documentation, public protocol symbols
and the corpus commit it verified against.
