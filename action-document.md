# Open-Sourcing & PyPI Publishing — Action Document

Working doc to drive the effort to make `testprotocols` (and `testoperations`)
a public, industry-standard project on PyPI. Captures decisions made, work
done, and what's left.

_Last updated: 2026-06-10_

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
| Inbound rights | **License-grant CLA** (ICLA + CCLA), Apache-derived, Alottabits as recipient | Gives Alottabits consolidated rights (future relicense/dual-license) while contributors keep copyright. DCO rejected — it grants no consolidated rights. |
| CLA acceptance | **Electronic, via CLA-assistant bot** on PRs | Lowest friction, auditable, scales. |
| CLA scope | **All current & future Alottabits projects** (sign once) | Avoids re-signing per repo as more packages are published. |
| PyPI auth | **Trusted publishing** (GitHub Actions OIDC), not stored tokens | No long-lived secrets to leak/rotate. Both names are unclaimed → register *pending* publishers. |
| Publish order | `testprotocols` **before** `testoperations` | `testoperations` depends on `testprotocols>=0.1.0`. |

## Done so far (uncommitted — sitting in the working tree)

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
- **CLA documents** (repo root) — drafts, pending counsel review:
  - `ICLA.md` — Individual CLA (Apache ICLA v2.2 adapted).
  - `CCLA.md` — Corporate CLA (Apache CCLA adapted) with Schedule A
    (designated employees) and Schedule B (initial contributions).
  - `CONTRIBUTING.md` — explains CLA flow + dev workflow (uv).
- **CLA bot** — `.github/workflows/cla.yml` using
  `contributor-assistant/github-action@v2.6.1`; signatures stored on an
  auto-created `cla-signatures` branch via `GITHUB_TOKEN`; sign phrase matches
  `CONTRIBUTING.md`; bots allowlisted.

## Remaining TODOs

### 1. Legal / CLA finalization
- [ ] **Counsel review** of `ICLA.md` and `CCLA.md`.
- [ ] Fill placeholders in both + `CONTRIBUTING.md`:
  - `[LEGAL ENTITY NAME]` — exact legal name/form (e.g. "Alottabits, Inc.")
  - `[GOVERNING LAW / JURISDICTION]`
  - `[NOTICES EMAIL]` — where corporate CLAs / questions go
- [ ] Decide signature storage: keep the `cla-signatures` branch (simple), or
      move to a **separate private repo + `PERSONAL_ACCESS_TOKEN`** secret for
      tamper-resistance (lines are commented in `cla.yml`).

### 2. Package metadata polish
- [ ] Add `authors` (or `maintainers`) to both `pyproject.toml`s.
- [ ] Add `[project.urls]` to both (Homepage, Repository, Issues) — shows on
      the PyPI project page.

### 3. Make the repo public
- [ ] Flip repo visibility to public on GitHub.
- [ ] **Enable Actions** and set Workflow permissions → "Read and write"
      (Settings → Actions → General) so the CLA bot can write.
- [ ] Verify the CLA bot end-to-end with a test PR (first run auto-creates the
      `cla-signatures` branch + signature file).

### 4. Trusted publishing setup
- [ ] On PyPI, register a **pending publisher** for **each** name
      (`testprotocols`, `testoperations`): owner `alottabits`, repo
      `testprotocols`, workflow `release.yml`, environment `pypi`.
- [ ] Write `.github/workflows/release.yml`:
  - Trigger on version tag push (`v*`).
  - `permissions: id-token: write` (required for OIDC — easy to forget).
  - `environment: pypi` (matches the pending publisher; allows approval gate).
  - Steps: checkout → setup-uv → `uv build` both packages → `uv publish`.

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
- The CLA workflow uses `pull_request_target` (needed so the bot can write from
  fork PRs). Keep it CLA-only — **never** add build/test steps that check out
  or run untrusted PR code there; those belong in a separate `pull_request`
  workflow.

## Reference

- Apache CLA templates: https://www.apache.org/licenses/contributor-agreements.html
- CLA Assistant action: https://github.com/contributor-assistant/github-action
- PyPI trusted publishing: https://docs.pypi.org/trusted-publishers/
- uv publishing guide: https://docs.astral.sh/uv/guides/publish/
- PEP 639 (license metadata): https://peps.python.org/pep-0639/
