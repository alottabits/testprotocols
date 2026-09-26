# Change proposals

A proposal is how a consumer of `testprotocols` / `testoperations` asks for
a change to the shared contracts. This page is the canonical statement of
the format, the cycle and what a proposal is judged against; the consumer
repositories point here. The reviewer's working method is not published
(CONTRIBUTING.md, "How this differs from a typical GitHub project").

## What enters a proposal

Interface vocabulary only: a capability protocol (a boundary view
included), an archetype extension, a WhiteBox extension, an operation. The
framing litmus: a function with logic of its own is an operation whatever
file it sits in; a forwarder or test plumbing is not, and never enters.

A new **device archetype** does not enter as a proposal. A consumer requests
one with the `archetype-request` issue template, and a maintainer runs it
through `docs/archetypes/README.md`.

## One document per originating use case

- Items are batched: one document per use case, however many items.
- The file is `docs/proposals/YYYY-MM-DD-<slug>.md`. The slug names the
  need in the domain's vocabulary, never the consumer or its use-case id.
- Branch `proposal/<slug>`, PR titled `proposal: <slug>`, opened with
  `?template=proposal.md`, *allow edits by maintainers* left on so the
  review can be appended in place.
- The PR adds that one file and nothing else; the `hygiene` job enforces
  it.

## Document format

Header table, first thing after the title:

| Field | Value |
| --- | --- |
| Date | YYYY-MM-DD |
| Use case | `<use-case id>` — one sentence on the goal |
| Round | 1 |
| Status | `under review` / `accepted` / `accepted with conditions` / `closed — consumer decision` |

Then one `### P<n> — <kind> <name>` block per item, with these headings in
this order:

- **Item**: `P1`, and the kind (capability protocol, boundary view,
  archetype extension, WhiteBox extension, operation, model).
- **Need**: what, and which existing protocols and operations were checked
  and why each fails.
- **Proposed design**: signature, models, framing rationale.
- **Placement**: **promote** to `testprotocols` or `testoperations`, or
  **keep local** with the trigger that would promote it. For a promote
  item: **plugin-staged** (a `PROMOTED_AS = "module:Symbol"` marker in the
  consumer) or **carried patch** (an `Upstream-Status:` header on a fork).
- **Affected**: existing symbols, consumers, drivers.
- **Neutrality evidence**: the domain's reviewed-family list, and how each
  family expresses the need. Vendor and tool names go here and nowhere
  else.

## The neutrality rule

This repository is public. No organisation or customer names, sites,
hostnames, addresses, people or ticket ids anywhere in the document;
vendor and tool names only inside Neutrality evidence; the originating
use-case id is allowed as a traceability key. Documentation uses the
RFC 5737 / RFC 3849 address ranges. A violation is a blocking condition
returned before any design question is answered.

## What a proposal is judged against

The review answers these questions, in this order, for every item:

0. **Neutrality.** Does the document meet the rule above? A miss ends the
   round here.
1. **Recorded decisions.** Is it in line with `docs/architecture/`,
   including recorded prior decisions? Reopening one needs new evidence,
   argued explicitly.
2. **Vendor and tool neutrality.** Does it hold against the domain's
   reviewed-family list, as recorded in the domain's design document? A
   domain with no recorded list gets a proposed list, presented as
   proposed, and ratifying it becomes a condition.
3. **Zero-contract-change alternative.** Can the need be met in the
   driver or plugin without changing a contract? Promote is earned, not
   the default.
4. **Correct home.** `testprotocols`, `testoperations`, or plugin-local?
5. **Overlap with capability protocols.** Is there an existing protocol or
   a sibling of one?
6. **Overlap with operations.** Is there an existing operation, or a
   consumer reconstructing one field by field?
7. **One consumer, and why now.** The GAPS freeze bar wants a test that
   needs the shape, ideally two consumers agreeing before the design
   freezes. A proposal from one consumer says what substitutes for the
   second: for a capability protocol, neutrality evidence across the
   domain's reviewed-family list is the accepted substitute; for an
   archetype core, the ratified family list, the sourced matrix and the
   reference corpus (`docs/archetypes/README.md`); for an archetype tier or
   a boundary view that folds several devices, a second consumer (or, for a
   tier, a second trigger family) is still required and the item defaults
   to plugin-staged or keep-local with the trigger recorded.
   **Corpus impact:** for an item that touches a capability reachable from
   an archetype in the reference corpus, the review states how many
   reference families could implement it. At or above the core threshold
   (every trigger family and a majority of the ratified list), the item is
   promoted on condition that every reference driver implements it before
   the `feat:` PR merges; below it, the item is a tier or optional member,
   or keep-local, and the count is the argument.

When the verdict hinges on a claimed vendor or tool behaviour, the review
verifies it against published documentation and cites what it checked.

## The review response

The review team posts one GitHub PR review whose body is:

```markdown
## Review response (testprotocols review team, YYYY-MM-DD)

| Item | Decision | Reason |
| --- | --- | --- |
| P1 | accept / accept with conditions / decline | one line |

### 0. Neutrality
...
### 7. One consumer, and why now
...

### Conditions
- C1 ...
```

Decisions per item are `accept`, `accept with conditions` or `decline`.
The PR-level verdict, which sets the `review` check, is `approve`,
`approve with conditions` or `request changes`. Conditions are numbered
`C1`, `C2`, ... and each names the item it binds.

The contributor, or a maintainer using *allow edits by maintainers*,
appends the block verbatim to the document after a `---` rule in the next
push. The agent never commits to the branch: authorship and sign-off stay
the contributor's. The document, not the PR conversation, is the record.

## The code and release reviews

A `feat:` or `fix:` PR is read by the code reviewer, a `release:` PR by the
release reviewer, against the same rule as proposals: the criteria are
public, the method is not. Each posts one review whose body is a
per-question table followed by one section per question and the
conditions, and sets the `review` status from the table. A PR that takes
two reviewers (a `feat:` that also touches a decision file) gets two
reviews, and the worst verdict sets the status.

**The code reviewer's questions**, in order:

1. **Proposal coverage.** Every shape change is covered by a merged
   proposal's accepted item (path and item id cited in the body), or the
   body says `no proposal` with a one-paragraph rationale.
2. **Conditions met.** Every condition the cited proposal's review recorded
   for an implemented item is met and cited.
3. **Contract rules.** `Protocol`-typed boundary, typed models, no vendor
   leakage into a shared contract, no sibling of an existing protocol or
   operation, no forwarder or test plumbing in either package.
4. **Tests for both outcomes.** Every new or changed symbol has a test for
   the positive path and one for the negative or edge path.
5. **Changelog entry.** Present under the right package and subsection, in
   the entry format, with a migration line for a breaking change.
6. **Neutrality** of code, comments, tests, fixtures and docstrings.
7. **Corpus coverage.** For a PR that touches a capability reachable from an
   archetype in the reference corpus: every new or changed member is
   implemented by every reference driver, each mapping cites its source,
   and an unsupported cell raises `NotSupportedError` with a source. The
   `conformance` status is the deterministic half; this question applies
   once a corpus archetype exists.

**The release reviewer's questions**, in order:

1. **Versions and the pin.** Both versions equal the title and the changelog
   heading; `testoperations` pins `testprotocols>=X.Y.Z,<X.(Y+1).0`.
2. **Bump severity.** MINOR if the released section has a breaking entry in
   either package, PATCH otherwise; never an empty section.
3. **Breaking entries complete.** Old shape, new shape, migration line, and
   *proposed as* where the merged path differs.
4. **Every merged change has an entry.** Every merge since the last tag that
   touched package source is cited; no entry cites an unmerged PR.
5. **Cited proposals exist** on `main`.

The response body:

```markdown
## Review response (testprotocols review team, YYYY-MM-DD) — code | release

| Question | Answer | Reason |
| --- | --- | --- |
| 1. ... | met / met with conditions / not met | one line |

### 1. ...
...

### Conditions
- C1 (Q4): ...
```

The verdict is `approve` when every row is `met`, `approve with
conditions` when none is `not met`, `request changes` otherwise. On a
`release:` PR only `approve` passes the `review` check; `approve with
conditions` sets it to failure.

## Rounds

The contributor answers with an **Outcome** section (per item: decision,
date) or one revision in place with the round set to 2 and the round-one
response left below. Two rounds. After round two without agreement:

- a keep-local item is the consumer's call, recorded with the maintainer's
  reservations verbatim;
- a declined promote item may be implemented locally, recorded as
  `consumer decision — implemented locally after decline` with the
  objection and resubmission conditions copied in. A later proposal that
  meets those conditions is a new document citing this one.

## Merge

A maintainer merges once every item has an Outcome, declined and
kept-local included. At merge the maintainer writes a pointer in
`packages/testprotocols/GAPS.md` for every keep-local trigger and every
declined item, naming the proposal path and its conditions; the `hygiene`
job checks on later `proposal:` and `release:`
PRs that the pointer exists.

A proposal whose contributor has gone silent for 60 days after a review is
**closed, not merged**: the maintainer comments `closed — contributor
inactive` and closes the PR. The document stays on its branch; the closed
PR records that the need was raised. Merged proposals are the corpus every
later review reads, and an unfinished document must not enter it. A later
proposal for the same need cites the closed PR.

## After the review

- The merged document is the design record.
- The implementation arrives as a `feat:` PR citing the proposal path and
  item ids; the code reviewer checks it against the recorded conditions.
- A live run that forces a change is recorded as a dated **Design delta**
  section appended to the merged document, in a `delta:` PR that touches
  that one file. A delta that changes no accepted contract is answered
  `records only, merge on sight`; one that changes an item's signature,
  models or placement gets the per-item table and an Outcome per changed
  item.
- A reshape at the implementation PR is recorded as a design delta in the
  same PR, and the changelog entry carries the *proposed as* field.

## Consumer-side conventions this repository recognises

- A **plugin-staged** addition declares `PROMOTED_AS = "module:Symbol"`;
  the merged symbol path in the changelog entry is the value the marker
  must carry after switch-over.
- A **carried patch** on a fork carries `Upstream-Status:` with one of
  `Pending`, `Submitted <PR url>`, `Backport <version>`,
  `Denied <reason>`, `Inappropriate <reason>`. A fork header in any other
  state is one this repository makes no promise about.
