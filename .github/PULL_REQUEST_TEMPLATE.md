<!-- Title: `<kind>: ...` — kinds and what each needs are in CONTRIBUTING.md.
     Proposal PRs: open with ?template=proposal.md for the document skeleton. -->

- [ ] Title carries a kind prefix (`proposal:`, `delta:`, `feat:`, `fix:`, `docs:`, `chore:`, `ci:`, `test:`, `release:`)
- [ ] Every commit is signed off (DCO)
- [ ] The local gate passes: `uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run pyright && uv run pytest`
- [ ] No organisation, customer, site, host, address, person or ticket identifiers (CONTRIBUTING.md, "Neutrality")
- [ ] `CHANGELOG.md` `[Unreleased]` entry added, or no package source touched

Proposal and item ids this PR implements, or `no proposal` with a one-paragraph rationale:

