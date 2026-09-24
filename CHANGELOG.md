# Changelog

All notable changes to `testprotocols` and `testoperations` are recorded
here, in [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) layout.
The two packages release in lockstep, so one section per version lists
both. Entries are written by the PR that makes the change, under
`[Unreleased]`, in the format CONTRIBUTING.md states (kind, merged symbol
path, one-line behaviour, proposal path and item, PR number, *proposed as*
where reshaped). A release PR renames `[Unreleased]` to the version and
adds a fresh empty `[Unreleased]` above it.

Versions before this file existed (0.9.0 to 0.12.1) are described by their
release commits and PR pages; a backfill is planned.

## [Unreleased]

### testprotocols

- no entries yet

### testoperations

#### Added

- **model member** `testoperations.waiting:ReachabilityAwait.retried` —
  whether more than one poll was needed to finish waiting, derived from
  `polls`. no proposal; PR #43.
