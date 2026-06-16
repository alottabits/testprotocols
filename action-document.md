# Open-Sourcing & PyPI Publishing — Action Document

Working doc to drive the effort to make `testprotocols` (and `testoperations`)
a public, industry-standard project on PyPI. Captures decisions made, work
done, and what's left.

_Last updated: 2026-06-16_

---

## Goal

Make the `alottabits/testprotocols` monorepo (packages `testprotocols` +
`testoperations`) an **industry-standard test resource layer**: relicense it
appropriately, set up contributor governance, make the GitHub repo **public**,
and publish both packages to **PyPI**.

## Decisions made

| Topic | Decision | Rationale |
| --- | --- | --- |
| License | **Apache-2.0** (relicensed from MIT) | Explicit patent grant + retaliation clause — important for adopter confidence in a standards-track project. Relicense was clean because all copyright was Alottabits-held. |
| Inbound rights | **Developer Certificate of Origin (DCO)** — inbound = outbound = Apache-2.0 | _Reversed the earlier CLA decision (2026-06-16)._ Alottabits will keep the code permanently open source with no relicense/dual-license intent, so a CLA's consolidated-rights benefit is moot. DCO gives a provenance paper trail with zero contributor friction and is the industry standard (Linux, Git, Docker). Tradeoff accepted: a future relicense would require re-contacting all contributors. |
| DCO acceptance | **`Signed-off-by` line per commit** (`git commit -s`), checked on every PR | No documents to sign/email; auditable via commit trailer; enforced by a DCO check. |
| PyPI auth | **Trusted publishing** (GitHub Actions OIDC), not stored tokens | No long-lived secrets to leak/rotate. Both names are unclaimed → register *pending* publishers. |
| Publish order | `testprotocols` **before** `testoperations` | `testoperations` depends on `testprotocols>=0.1.0`. |

## Done so far (committed to `main`)

The relicense + contributor-governance work landed on `main` in commit
`11954ac chore: relicense to Apache-2.0 and add contributor governance`. The
PyPI metadata polish, release workflow, and the DCO governance switch are on
branch `chore/pypi-release-workflow` (off current `main`). The old
`chore/apache-relicense-cla-pypi-prep` branch was stale and has been deleted
(local + remote).

- **Relicense to Apache-2.0**
  - Root `LICENSE` replaced with full Apache-2.0 text; root `NOTICE` added.
  - `LICENSE` + `NOTICE` copied into `packages/testprotocols/` and
    `packages/testoperations/` so each wheel carries them.
  - Both `pyproject.toml`s: PEP 639 `license = "Apache-2.0"` +
    `license-files = ["LICENSE", "NOTICE"]`, classifier set added, build
    backend bumped to `setuptools>=77.0`.
  - Verified via `uv build --package testprotocols`: wheel METADATA shows
    `License-Expression: Apache-2.0` and both license files bundled under
    `dist-info/licenses/`.
- **Contributor governance = DCO** (branch `chore/pypi-release-workflow`)
  - Replaced the CLA approach with the Developer Certificate of Origin.
    Deleted `ICLA.md`, `CCLA.md`, and the CLA-assistant workflow
    `.github/workflows/cla.yml`.
  - `CONTRIBUTING.md` rewritten to explain the DCO: `Signed-off-by` per commit
    (`git commit -s`), inbound = outbound = Apache-2.0, link to
    developercertificate.org.
  - _Historical note:_ the original commit `11954ac` on `main` added the CLA
    docs + bot; this branch supersedes that governance choice.
- **Package metadata polish** (branch `chore/pypi-release-workflow`)
  - Both `pyproject.toml`s now carry `authors` + `maintainers`
    (`Alottabits <rjvisser@alottabits.com>`) and a `[project.urls]` table
    (Homepage, Repository, Issues → `github.com/alottabits/testprotocols`).
  - Verified in the built wheels: METADATA shows `Author-email`,
    `Maintainer-email`, and the three `Project-URL` entries;
    `testoperations` still records `Requires-Dist: testprotocols>=0.1.0`.
- **Release workflow** — `.github/workflows/release.yml`
  - Triggers on `v*` tag push; `permissions: id-token: write`;
    `environment: pypi`. Builds both packages with `uv build --package`, then
    `uv publish`es `testprotocols` before `testoperations` (trusted publishing,
    automatic OIDC, no stored token).

## Remaining TODOs

### 1. Contributor governance (DCO) — mostly done
- [x] Adopt DCO; remove CLA docs + CLA bot; rewrite `CONTRIBUTING.md`.
- [x] **DCO enforcement = in-repo workflow** `.github/workflows/dco.yml`
      (chosen over the org-level DCO GitHub App so enforcement is confined to
      this repo and version-controlled). Self-contained shell check on
      `pull_request`; verifies a well-formed `Signed-off-by` trailer on every
      non-merge commit. No third-party action beyond `actions/checkout`.
- [ ] Once the repo is public, mark the **`dco` check required** in branch
      protection (Settings → Branches) so PRs can't merge without it.
- [ ] (Optional) Quick legal sanity-check that DCO + Apache-2.0 inbound = outbound
      matches Alottabits' intent — far lighter than the CLA counsel review, but
      worth a glance. No bespoke agreement text to review anymore.

### 2. Package metadata polish — ✅ done
- [x] Add `authors` (or `maintainers`) to both `pyproject.toml`s.
- [x] Add `[project.urls]` to both (Homepage, Repository, Issues) — shows on
      the PyPI project page.

### 3. Make the repo public
- [ ] Flip repo visibility to public on GitHub.
- [ ] **Enable Actions** (Settings → Actions → General) so `release.yml` can run.
      DCO via the GitHub App needs no special workflow permissions; an in-repo
      `dco.yml` only needs the default read token.
- [ ] Verify DCO enforcement with a test PR: an unsigned commit should be
      blocked, and `git commit --amend -s` (or `--signoff` rebase) should clear it.

### 4. Trusted publishing setup
- [ ] On PyPI, register a **pending publisher** for **each** name
      (`testprotocols`, `testoperations`): owner `alottabits`, repo
      `testprotocols`, workflow `release.yml`, environment `pypi`.
- [x] Write `.github/workflows/release.yml` — done on
      `chore/pypi-release-workflow`. Triggers on `v*`; `id-token: write`;
      `environment: pypi`; builds both via `uv build --package`, then
      `uv publish`es `testprotocols` then `testoperations`.
- [ ] On GitHub, create the `pypi` **Environment** (Settings → Environments)
      if you want the manual approval gate the workflow references.

### 5. First release
- [ ] Bump versions in both `pyproject.toml`s as needed (currently `0.1.0`).
- [ ] Rehearse on **TestPyPI** first (`uv publish --index testpypi`), then
      verify a clean install in a throwaway env.
- [ ] Tag (`v0.1.0`) and push → release workflow publishes `testprotocols`
      then `testoperations`.

## Notes / gotchas

- A published PyPI version is **immutable** — you can yank but never re-upload
  the same version. Rehearse on TestPyPI.
- `testoperations/pyproject.toml` has `[tool.uv.sources] testprotocols =
  { workspace = true }` — a uv-local dev override that `uv build` strips from
  published metadata, leaving the real `testprotocols>=0.1.0` dependency. Only
  works once `testprotocols` is actually on PyPI.
- DCO sign-off requires the commit author's **real name and a reachable email**
  in the `Signed-off-by` trailer; `git commit -s` fills it from `user.name` /
  `user.email`. Squash-merging a PR can drop per-commit trailers — keep merge
  commits or ensure the squashed message retains a sign-off.

## Reference

- Developer Certificate of Origin: https://developercertificate.org/
- DCO GitHub App: https://github.com/apps/dco
- PyPI trusted publishing: https://docs.pypi.org/trusted-publishers/
- uv publishing guide: https://docs.astral.sh/uv/guides/publish/
- PEP 639 (license metadata): https://peps.python.org/pep-0639/
