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
| 0 | Request | issue from the `archetype-request` template | maintainer | a charter is opened, or the request is declined on the issue with the reason |
| 1 | Charter | PR `charter: <slug>`, merged to `main`; adds the document with Status `chartered` and only its Charter section | archetype reviewer, charter questions | merge ratifies the class definition and the reviewed-family list; it commits scope only, no contract |
| 2 | Exploration | branch `archetype/<slug>`, no PR | none | the maintainer opens the design PR |
| 3 | Design | PR `archetype: <slug>`, the document only | archetype reviewer, design questions; two rounds | verdict not `request changes`, every manifest row has an Outcome, Status `accepted for verification`; **not merged** |
| 4 | Verification | the same PR gains the core code, tests and changelog entries; a reference driver per ratified family is written in the private corpus | code reviewer and archetype reviewer, verification questions | `conformance` green; every finding folded back into the document in place and recorded in its review record |
| 5 | Land | merge with Status `verified`; then a `release:` | release reviewer | tag, publish |

Nothing but the charter reaches `main` before verification: an accepted
design on `main` is a recorded decision every later review reads.

A tier left `tier-staged` becomes a GAPS pointer at merge. When its trigger
fires (a second consumer or a second trigger family), it arrives through an
ordinary `proposal:` citing the design path and row id, and its reference
drivers arrive with the implementing `feat:` PR.

A charter that cannot be agreed after two rounds is closed, not merged. A
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
5. **Reuse vs. net-new** — every net-new protocol or field justified against
   reuse, derivation and composition; a shared-with table per sibling
   archetype.
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

| Id | Kind | Symbol | Placement | Breaking | Outcome |
| --- | --- | --- | --- | --- | --- |
| M1 | new protocol / new field / new archetype / new tier / rename / SPLITS entry / GAPS entry / LEVELS entry | `module:Symbol` | `core` or `tier-staged — <trigger>` | yes / no | accepted / accepted with conditions / declined, date |

Every symbol change the body mentions has a row. `core` rows are implemented
on the `archetype:` PR and get changelog entries citing `<design path> M<n>`.
`tier-staged` rows get a pointer in `packages/testprotocols/GAPS.md` naming the
document before the PR merges at `verified`. A later `feat:` PR cites a row
the way it cites a proposal's `P<n>`.

## The evidence bar

For an archetype **core**, a ratified reviewed-family list plus the sourced
matrix plus the reference corpus substitutes for a second consumer. A core
member is supported on every trigger family and on a majority of the ratified
list; anything else is a tier or a documented per-method unsupported case. A
**tier** still waits for a second consumer or a second trigger family.

## The reference corpus and the `conformance` check

The maintainers keep a **private** reference corpus: one reference driver per
ratified family, written against the family's published documentation in the
shape a real driver takes (a `VitroDevice` with the family's transports as
routes and one implementation per capability). Every method carries out the
family's published operation and cites its source; an unsupported cell raises
`NotSupportedError` with the source of the absence. The drivers validate the
**shape** — that the proposed methods map onto each family's way of working —
not driver behaviour, and they are never run against a device.

The corpus is kept current with every archetype that went through this track:

- a change that **extends** such an archetype is promoted only when enough
  families can implement it (the core threshold above), and a maintainer adds
  it to every reference driver before the change merges;
- a change that **narrows** it shows which families no longer satisfy it.

The `conformance` status reports this on every PR that changes package
source, in public terms only: the public symbol and the number of families,
never the corpus content. A pull request from a fork gets `conformance` when a
maintainer runs `/review`. `conformance` becomes a required check when the
corpus pipeline is live; CONTRIBUTING.md lists the required checks. The
review record of a verified design names the corpus commit it was verified
against.

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
4. **Demand.** The request's test intents map onto the charter's operations.

**Design** (`archetype:` PR, document only):

0. **Neutrality.** Vendor names only in the evidence sections.
1. **Recorded decisions.** In line with `docs/architecture/`, SPLITS, LEVELS
   and the capability-only rule; reopening needs new evidence.
2. **Matrix soundness.** Every cell sourced; denominators against the ratified
   list; every ◐ a verification item.
3. **Reuse exhausted.** Every net-new protocol or field justified against
   reuse, derivation and composition.
4. **Core vs. tiers.** Every core member meets the core threshold; everything
   else is `tier-staged` with its trigger, or a documented per-method
   unsupported case.
5. **Levels.** Sea-level vs. white-box per LEVELS.md; no vendor terms in method
   names at any level.
6. **No siblings.** No near-duplicate of an existing protocol; renames flagged
   breaking.
7. **Manifest complete.** Every symbol change in the body has a row with its
   breaking flag and tracking-file entries.

**Verification** (`archetype:` PR with package source):

1. **Coverage.** One reference driver per ratified family, pinned to the PR
   head; `conformance` green.
2. **Real mappings.** Every method carries out the family's published
   operation and fills the neutral model, citing its source; unsupported
   cells raise `NotSupportedError` with a source and nothing else. Citations
   are sampled against the published documentation.
3. **Matrix agreement.** ✓ is an implemented method, ◐/✗ is unsupported; a
   mismatch names which side is wrong.
4. **Faithful mapping.** No vendor data carried in loosely typed fields; every
   lossy mapping recorded in the document.
5. **Findings folded back** into the matrix, body, manifest and review record.

The posted review cites only public documentation, public protocol symbols
and the corpus commit it verified against.
