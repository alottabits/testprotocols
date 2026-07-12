# Design: `testoperations` criteria-driven selection + poll-until-converge waiting

| Field   | Value                                                              |
| ------- | ------------------------------------------------------------------ |
| Status  | Implemented (0.5.0)                                                |
| Author  | rjvisser                                                           |
| Date    | 2026-07-12                                                         |
| Related | `packages/testoperations/src/testoperations/selection.py`, `waiting.py`, `throughput.py` (the `measure_path_until` seam style these follow), `packages/testprotocols/src/testprotocols/network_probe.py` |

## Purpose

Two generic mechanics recur in acceptance suites built over these packages
and had accumulated as suite-local copies downstream:

1. **Poll-until-converge.** Distributed-system state (route propagation,
   policy pushes, log delivery) is eventual; tests observe it by polling a
   boolean signal until it reads the wanted way or a time budget lapses.
2. **Criteria-driven candidate selection.** A portable scenario declares the
   state its device-under-test must already be in as a criteria table
   (`attribute → wanted state`) and resolves ONE candidate matching the WHOLE
   spec atomically — evaluating every criterion together per candidate
   prevents split resolution, where two criteria silently bind to two
   different devices.

`testoperations` 0.5.0 graduates both as assertion-free composition
functions. Verdicts, budgets, vocabularies, and failure phrasing stay with
the caller.

## `waiting.py`

- `wait_until(predicate, *, budget_s, interval_s, sleep=time.sleep,
  monotonic=time.monotonic) -> bool` — the shared skeleton: poll
  `predicate()` until `True` or the budget lapses; returns whether the wanted
  verdict was observed, never raises on expiry. The predicate is always
  evaluated at least once. Injected clocks make the loop unit-testable
  (the same seam style as `throughput.measure_path_until`). The loop is
  deliberately synchronous and single-threaded; callers may rely on that
  (e.g. found-slot closures that capture the matching observation).
- `probe_reachable(probe: NetworkProbe, proto, target_ip, *, tcp_port=5201,
  udp_port=5201) -> bool` and `wait_for_reachability(...)` — the icmp/tcp/udp
  dispatch and its poll, typed against the `NetworkProbe` protocol directly
  so any device exposing the capability can use them. UDP verdicts require a
  responder at the target (see the protocol's docstring); arranging one is
  the caller's concern. Port defaults follow the iperf3 convention.

## `selection.py`

Generic over the candidate type `T`; the *vocabulary*
(`Mapping[str, Callable[[T], str]]`) maps each attribute name to a reader
returning the candidate's current state string, so no device types enter the
module and per-program semantics (what "filtered" or "baseline" means) stay
with the caller.

- `criterion_matches(want, got)` — equality plus one comparator, `>= N`
  (numeric minimum); a non-numeric observation never satisfies it.
- `validate_criteria(criteria, vocabulary)` — fail-closed on attributes
  outside the vocabulary; raises `UnknownCriteriaError(unknown, known)`
  (both pre-sorted).
- `first_mismatch(candidate, criteria, vocabulary)` — the first failing
  `(attr, want, got)`, or `None` on a full match. Exposed separately so
  callers with an extra, non-vocabulary eligibility stage can keep the same
  atomic evaluation loop.
- `select_one(candidates, criteria, vocabulary, *, describe)` — validates,
  then binds the FIRST full match in caller order (ordering, and therefore
  rerun determinism, is the caller's contract). On no match raises
  `NoMatchingCandidateError(failures)` carrying each candidate's first
  mismatch as `CandidateMismatch(candidate, attribute, want, got)`, labelled
  via `describe`.

## Error model

`testoperations` stays assertion-free: the engine raises typed,
data-carrying exceptions and never `AssertionError`. Consumer suites convert
them into their own precondition-failure phrasing — mechanic in the library,
verdict with the caller. Exception payloads are structured (sorted name
lists, mismatch dataclasses) precisely so callers can reproduce their
existing failure texts byte-for-byte.

## Non-goals

- Discovery (building the candidate list) is per-program selection policy
  and stays with the consumer.
- Domain-specific poll bindings whose signal contracts live outside these
  packages (e.g. log-taxonomy reads) stay downstream until the usual
  ≥2-consumer evidence justifies a shared contract; they compose over
  `wait_until` unchanged.
