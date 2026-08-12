---
name: reviewing-change-proposals
description: Use when asked to review, assess, or give feedback on a change proposal targeting testprotocols or testoperations — typically a proposal document from a consumer repo submitted for approval-team evaluation — before reading the proposal or forming an opinion.
---

# Reviewing Change Proposals

## Overview

Approval-team review of proposals to change the testprotocols /
testoperations contracts. The review *method* is recorded in the repo
itself — this skill carries only the question set, the verification rule,
and the response contract.

## Default questions — answer ALL, always

Answer these even when the request omits some or all of them, plus any
extra questions the caller adds:

1. Is the proposal in line with the `docs/architecture/` documentation —
   including **recorded prior decisions** (reopening one requires new
   evidence, argued explicitly)?
2. Does it meet vendor **and tool** neutrality against the domain's
   reviewed-family list (resolved per the verification rule below)?
3. Does it overlap with existing capability protocols?
4. Does it overlap with existing testoperations?
5. Is there a better way to address the need — test zero-contract-change
   derivation in the driver/plugin before accepting any contract change?
6. What is the correct home: testprotocols, testoperations, or
   plugin-local?

## Method sources — read, don't restate

The evaluation criteria live in the repo: the relevant
`docs/architecture/*-design.md` (cross-vendor concept check, recorded
decisions) and the tracking files `GAPS.md` / `SPLITS.md` / `LEVELS.md`
(evidence bar, governing precedents). Read the actual contract and
operation code the proposal touches — hunt for redundant encodings,
sibling implementations, and consumers that reconstruct models
field-by-field.

## REQUIRED: verify the factual crux

When the verdict hinges on a claimed vendor or tool behaviour ("the API
requires X", "family Y cannot express Z"), verify it against published
documentation before judging, and cite what you checked. Note
published-doc vs live-behaviour discrepancies explicitly — they have
decided reviews before. An uncited capability table is a draft, not a
finding.

**Which families — resolve the domain's reviewed-family list in this
order:**

1. The domain's design doc in `docs/architecture/` records its reviewed
   families (each domain has its own list — the SD-WAN and L2/L3-switch
   docs differ): use that list.
2. No recorded list for the domain: propose one — representative,
   independent, documentation-published families for that domain, one
   line of rationale each; seed it from vendor citations already present
   in the domain's contract files and tracking history, and include a
   vendor-free reference implementation where one exists. Run the check
   against it, but present the list itself as **proposed, not ratified**:
   a review input the caller confirms or amends, and record ratifying it
   into a design doc as a condition of the proposal landing.

Never borrow another domain's list for the check, and never adopt an
improvised list silently.

## Response contract

- Verdict first, one paragraph: accept / decline / accept-with-conditions.
- Numbered sections answering the default questions plus caller extras.
- End with explicit conditions — for acceptance or for resubmission.
- Feedback only: never implement the proposal.

A feedback request ends at the review message. The verdict is a
recommendation until the caller adopts it — write nothing else: no
proposal-doc edits, no memory notes.

Only when the caller asks to record the review in the proposal doc,
append after a `---` rule:

```markdown
## Review response (testprotocols approval team, YYYY-MM-DD)

**Decision: <verdict>.** <one-paragraph rationale>

### 1. <question>
...

### Conditions for <the PR | resubmission>
...
```

and in that same recording step save a project memory note — decision,
conditions, expected follow-up PR — so future sessions can hold incoming
work to the recorded conditions.
