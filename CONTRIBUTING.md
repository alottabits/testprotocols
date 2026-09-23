# Contributing to testprotocols / testoperations

This repository owns the contracts several test beds pin, and it owns the
process its consumers follow to change them. This page is that process,
from a first pull request to a released symbol. Two other pages carry the
parts that have their own shape: `docs/proposals/README.md` for the
proposal format and cycle, and `SECURITY.md` for private reports.

## How this differs from a typical GitHub project

- **Agents are the independent reviewers; a maintainer's merge is the
  human go-ahead.** Every reviewed PR is read by the project's review
  team, which posts one review and sets the `review` check. A maintainer
  then reads that review and merges. There is no approval button in the
  path: GitHub cannot express "one approval, the author may self-approve",
  so the merge is the approval and only maintainers can merge.
- **Zero required approving reviews**, for the reason above; branch
  protection enforces the checks and restricts who may push instead.
- **`/review` is maintainer-only.** It spends model budget and touches
  secrets, so only a handle listed in `MAINTAINERS.md` can trigger it. This
  is a spend and secret-exposure control, not a judgement on contributors.
- **Authoring and reviewing agents never share a session.** The agents
  that draft proposals or code in a consumer repository are not the agents
  that review here; the reviewer runs from its own checklist with no
  authoring transcript. Agents never merge and never push to a
  contributor's branch.
- **Two rounds** on a proposal, then the consumer decides (see the
  proposals README).
- **The maintainer's three-line glance.** Before merging, the maintainer
  reads the neutrality answer, the per-item table or the changelog entry,
  and one finding they agree with or override.
- **Criteria public, method private.** What a change is judged against is
  published in this repository (`docs/proposals/README.md` and the
  reviewer tables below). How the reviewer works through those questions
  is not. The reviewer runs in a private repository so that its working
  method never appears in this repository's public workflow logs; the
  review and the status arrive under a GitHub App's identity.

## Developer Certificate of Origin (DCO)

To keep the project legally safe and permanently open source, we use the
[Developer Certificate of Origin](https://developercertificate.org/) (DCO) —
the same lightweight process used by the Linux kernel, Git, and Docker. There
is no separate agreement to sign and nothing to email.

The DCO is a statement that you wrote the contribution (or otherwise have the
right to submit it) and that you agree to license it under the project's
inbound license, **Apache-2.0**. Inbound equals outbound: your contributions
are offered under the same terms as the project itself, which keeps the code
open source and the provenance clear. You retain copyright in your work.

### How to sign your work

Add a `Signed-off-by` line to each commit message, using your real name and an
email you can be reached at:

```text
This is my commit message

Signed-off-by: Jane Doe <jane.doe@example.com>
```

Git can add this for you — just pass the `-s` / `--signoff` flag when you
commit:

```bash
git commit -s -m "Your message"
```

By adding the sign-off you certify the statements in the DCO. **Every commit in
a pull request must be signed off.** If you forget, amend the most recent
commit with `git commit --amend -s`, or sign off a whole branch against `main`
with `git rebase --signoff main`.

A DCO check runs on every pull request and will flag any commit missing a valid
`Signed-off-by` line, with instructions on how to fix it.

## Development workflow

This is a [uv](https://docs.astral.sh/uv/) workspace with two packages under
`packages/`. To get started:

```bash
uv sync                       # install all workspace packages + dev tools
uv run pytest                 # run the test suite
uv run ruff check .           # lint
uv run ruff format --check .  # format check
uv run mypy .                 # type-check (strict)
uv run pyright                # type-check (strict, second checker)
```

Please make sure tests, linting, and type checks pass before opening a pull
request, and add tests for new behavior. The `Lint` workflow runs exactly these
commands on every pull request, so anything that fails locally fails there too.

Both type checkers are run because they disagree usefully: pyright reports
implicitly-`Any` ("unknown") types that mypy accepts, which is what keeps the
test fakes and the JSON-parsing helpers honestly typed. Both are pinned by
`uv.lock`; bump them deliberately in their own pull request rather than letting
a release change what CI enforces.

## Roles

| Role | Who | May |
| --- | --- | --- |
| Contributor | anyone with a GitHub account | open PRs of any kind; append an Outcome to their own proposal |
| Maintainer | listed in `MAINTAINERS.md`, mirrored in `.github/CODEOWNERS` | trigger a review, merge, tag, cut a release, write a GAPS pointer, override a review verdict with a recorded reason |
| Review team | the agents behind the `review` check, one per PR kind, run in the maintainers' private runner | post reviews and set the `review` status; never merge, never push |

## PR kinds

The title's prefix names the kind; `hygiene` rejects a title without one.

| Prefix | Meaning | Reviewer | Merge condition |
| --- | --- | --- | --- |
| `proposal: <slug>` | one new document at `docs/proposals/YYYY-MM-DD-<slug>.md` | proposal reviewer | every item has an Outcome |
| `delta: <slug>` | a dated **Design delta** section appended to a merged proposal; touches that one file | proposal reviewer | `records only, merge on sight`, or as `proposal:` when a contract changed |
| `feat: <scope>: <summary>` (`feat!:` when breaking) | implementation of accepted items, or a maintainer addition; the body cites the proposal path and item ids, or says `no proposal` with a one-paragraph rationale | code reviewer | verdict not `request changes`; changelog entry present |
| `fix: <scope>: <summary>` | behaviour fix, no shape change | code reviewer | as `feat:` |
| `docs:`, `chore:`, `ci:`, `test:` | nothing under `packages/*/src/` and none of the decision files | hygiene only | hygiene green |
| `release: X.Y.Z` | the version bump | release reviewer | verdict `approve` |

**Decision files override the prefix.** `docs/architecture/*.md`,
`packages/testprotocols/GAPS.md`, `SPLITS.md` and `LEVELS.md` are the
recorded decisions reviews are answered against. A PR that touches any of
them takes the proposal reviewer whatever its prefix, and `hygiene` does
not set the `review` status for it. A `feat:` PR that also adds a SPLITS
or LEVELS entry takes both the code and the proposal reviewer; the worse
verdict wins.

**Proposal first.** A `feat:` PR that changes a public symbol's shape
without a merged proposal is not merged. The code reviewer's first
question is whether the diff is covered by a merged proposal or is a
maintainer change with `no proposal` and its rationale.

## A PR's life

1. **Open.** Branch from `main`: `proposal/<slug>`, `feat/<slug>`,
   `fix/<slug>`, `release/X.Y.Z`. Commits signed off. A draft is fine; the
   deterministic gates run on it, `/review` on a draft is refused.
2. **Deterministic gates on every push:** `dco`, `lint`, `hygiene`. All
   three green before a review is requested.
3. **Review requested.** A maintainer comments `/review`. The reviewer
   for the kind runs, posts one PR review, sets the `review` status on the
   head commit. (The proposal reviewer is wired in: `proposal:`, `delta:` and
   decision-file PRs are reviewed by the agent. For `feat:`, `fix:` and
   `release:` PRs the maintainer still reads the PR against the same
   criteria and records the reading in a comment until the code and
   release reviewers land; a `/review` on those kinds is answered with a
   `review` status of `error` naming that.)
4. **Rework.** Push fixups; a new head commit clears the status; a
   maintainer comments `/review` again once the gates are green. Fixup
   commits may stay; the merge commit groups the PR. No interactive
   rebase is asked of you.
5. **Go-ahead.** A maintainer reads the review and merges with a merge
   commit. Merging over a `request changes` verdict needs a comment naming
   the finding and the reason, and may carry the `review-overridden`
   label.
6. **Record.** For a proposal, the document. For code, the PR page, which
   the changelog entry cites by number.

## The hygiene gate

`hygiene` runs on every push, with no agent, from this repository's
`main` (it never checks out your branch; it reads the PR through the API):

- the title has a recognised kind prefix;
- a PR that changes files under `packages/*/src/` also changes
  `CHANGELOG.md`, unless it carries the `skip-changelog` label;
- a `proposal:` PR adds exactly one file under `docs/proposals/`, named
  `YYYY-MM-DD-<slug>.md`, with the header table and a `### P1` block, and
  touches nothing else; a `delta:` PR modifies exactly one existing file
  there; a new document there enters only through a `proposal:` PR, and a
  `docs:`, `chore:`, `ci:` or `test:` PR may not change one; a `feat:`, `fix:`
  or `release:` PR may carry the in-PR design delta on the proposal it
  implements;
- a `release:` PR sets both version fields to the title's version and
  renames the `[Unreleased]` heading to it, with a fresh `[Unreleased]`
  above;
- on `proposal:` and `release:` PRs, every merged proposal whose Outcome
  has a keep-local or declined item has a pointer in
  `packages/testprotocols/GAPS.md`;
- a **neutrality scan** over the added lines of the diff (below).

For `docs:`, `chore:`, `ci:` and `test:` PRs that touch no package source
and no decision file, `hygiene` sets the `review` status itself
(`no agent review for this kind`), so such a PR needs no `/review`.

## Neutrality

This repository is public. Nothing in it names an organisation, a
customer, a site, a host, an address, a person or a ticket, in code,
comments, tests, docstrings or documents. Vendor and tool names appear
only as neutrality evidence in proposals and design documents. The
originating use-case id (`UC-nnn`) is allowed as a traceability key.

The scan in `scripts/neutrality_scan.py` fails a PR on: IPv4/IPv6 literals
outside the RFC 5737 / RFC 3849 documentation ranges (RFC 1918 and the RFC
2544 benchmarking range are tolerated under `tests/`); hostnames under
`.local`, `.lan` or `.internal`; e-mail addresses outside the example domains;
ticket-shaped ids (two or more capitals, a dash, digits) other than the
allowed prefixes listed in the script. The script carries no names on purpose;
the semantic check is the reviewers'. Use `192.0.2.0/24`, `198.51.100.0/24`,
`203.0.113.0/24`, `2001:db8::/32` and `example.com`.

When the scan is wrong about a line that must carry such a token (a vendor
model number in neutrality evidence, a standards document, an address in a
documented range the rule does not know), end that line with
`neutrality: allow` (as a comment in code, `<!-- neutrality: allow -->` in
Markdown); the marker is visible in the diff the reviewers read. A
maintainer may instead apply the `neutrality-override` label to the PR,
with the reason as a PR comment. In Python files the hostname rule reads
string literals, comments and docstrings only, since `.lan` and friends are
ordinary attribute names in this codebase.

## Versioning

Both packages carry one version, `0.MINOR.PATCH`, always equal.

| Bump | When |
| --- | --- |
| MINOR | the release contains at least one entry under *Breaking for driver authors* in either package: a new mandatory protocol member, a retype, a rename, a removal, a moved symbol |
| PATCH | everything else: new protocols, views, archetypes, operations, models; compatible changes; fixes |

Consumers pin `testprotocols>=0.M.P,<0.(M+1).0`; a PATCH never breaks a
driver that type-checks today. `testoperations` pins `testprotocols` the
same way from its first release under this process. The MAJOR digit stays
0 until the contracts are declared stable, by a proposal of its own.

## The changelog

`CHANGELOG.md`, Keep-a-Changelog layout, one `[Unreleased]` section.
The PR that makes a change writes its entry, under the package and the
subsection that applies (*Breaking for driver authors*, *Added*,
*Changed*, *Deprecated*, *Fixed*, *Consumer action*). One entry per item:

```markdown
- **capability protocol** `testprotocols.overlay:OverlayAdvertisements` —
  read the overlay subnets a site advertises, keyed by subnet.
  Proposal `docs/proposals/2026-08-23-overlay-advertisements.md` P1; PR #31.
```

Fields in order: kind; the **merged** importable path in `module:Symbol` form;
one line of behaviour (for Breaking and Changed: old shape, new shape,
migration line); the proposal path and item id, or `no proposal`; the PR
number; a *proposed as* field naming the old symbol path, only when the
maintainer reshaped the item at the PR. A `delta:` that changes a contract
before the release updates the item's existing entry.

## Releases

Cut on demand by a maintainer when every promote item of the triggering
use case is on `main`, when a consumer needs a released fix, or when a
breaking entry has waited long enough. Never per merged PR, never with an
empty `[Unreleased]`. A merged PR is in the next release without
exception; a change that must wait stays unmerged.

1. Branch `release/X.Y.Z` from `main`; bump both version fields and the
   `testoperations` pin on `testprotocols`; rename `## [Unreleased]` to
   `## [X.Y.Z] — YYYY-MM-DD` and add a fresh empty `[Unreleased]` above;
   commit `release: X.Y.Z`, signed off.
2. Open the PR `release: X.Y.Z`; `hygiene` checks the mechanics;
   `/review` runs the release reviewer.
3. Merge. The merge commit is the release commit.
4. Tag it `vX.Y.Z` (annotated, message `Release X.Y.Z`) and push the tag;
   `release.yml` publishes both packages behind the environment approvals.

A tag is never moved or deleted. A broken release is yanked on PyPI and
followed by a PATCH; the yank is noted in the changelog section. Fixes
land on `main` first; there are no stable branches at 0.x, and a consumer
that cannot take the next release carries the fix as a `Backport` patch.
A removal or rename is preceded by a *Deprecated* entry where the two can
coexist, and removed no earlier than the next MINOR.

## Branch protection on `main`

Applied by a maintainer and recorded here so it can be re-applied:
required checks `dco`, `lint`, `hygiene` (and `review` once the review
team is required); strict up-to-date off; required approving reviews 0;
push restricted to maintainers; conversation resolution required; force
pushes and deletions off; merge commits only; rules enforced for admins.

## Questions

Open an issue with the `question` label. A proposal is not a question;
see `docs/proposals/README.md`.
