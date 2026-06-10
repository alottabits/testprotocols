# Contributing to Alottabits Test Protocols

Thanks for your interest in contributing. This project aims to be a shared,
industry-standard test resource layer, so we ask every contributor to agree
to a Contributor License Agreement (CLA) before we can merge their work.

## Contributor License Agreement (CLA)

To keep the project's licensing clean and to allow Alottabits to steward the
project on behalf of the community, all contributions must be covered by a
CLA. The CLA confirms that you have the right to contribute your code and
that you grant Alottabits and the project's users a broad license to use it.
You retain copyright in your contributions.

There are two agreements:

- **[Individual CLA](ICLA.md)** — for contributions you make as yourself.
- **[Corporate CLA](CCLA.md)** — for contributions made on behalf of your
  employer. If your employer owns intellectual property you create, an
  authorized representative should sign the Corporate CLA, and you should be
  listed among its designated employees.

One signed CLA covers your contributions to **all current and future
Alottabits open-source projects** — you do not need to re-sign per
repository.

### How acceptance works

When you open your first pull request, an automated CLA assistant will check
whether your CLA is on file. If it is not, the bot will comment on the pull
request with a link to the agreement. To sign, post this exact comment on the
pull request:

> I have read the CLA Document and I hereby sign the CLA

Your acceptance is recorded electronically against your GitHub identity (full
name, email, and account), along with the date and time — that record serves
as your signature. If the check does not update, comment `recheck` to re-run
it. One signature covers all your future contributions to Alottabits
projects.

For the Corporate CLA, an authorized representative must first return the
signed agreement to [NOTICES EMAIL] before designated employees' pull
requests can be merged.

> The CLA documents in this repository are drafts pending legal review.
> Final, executed versions govern any actual contribution.

## Development workflow

This is a [uv](https://docs.astral.sh/uv/) workspace with two packages under
`packages/`. To get started:

```bash
uv sync                 # install all workspace packages + dev tools
uv run pytest           # run the test suite
uv run ruff check .     # lint
uv run ruff format .    # format
uv run mypy .           # type-check (strict)
```

Please make sure tests, linting, and type checks pass before opening a pull
request, and add tests for new behavior.
