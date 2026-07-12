"""Criteria-driven candidate selection engine.

A test declares the state its device-under-test must already be in as a
criteria table (``attribute -> wanted state``) and resolves ONE candidate
matching the WHOLE spec atomically — every criterion evaluated together per
candidate, so multiple candidates can never bind inconsistently (the
split-resolution defect this primitive exists to prevent).

The engine is generic over the candidate type ``T``: the *vocabulary* maps
each attribute name to a reader returning that candidate's current state
string, and readers close over whatever they need — no device types enter
this module. The CALLER owns candidate ordering (determinism rules), the
vocabulary (per-program semantics), and the verdict phrasing: on failure the
engine raises typed, data-carrying errors, never ``AssertionError``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass


class SelectionError(Exception):
    """Base for selection failures (criteria or candidate resolution)."""


class UnknownCriteriaError(SelectionError):
    """The criteria name attributes outside the vocabulary (fail closed)."""

    def __init__(self, unknown: list[str], known: list[str]) -> None:
        self.unknown = unknown
        self.known = known
        super().__init__(f"unknown criteria {unknown}; known attributes: {known}")


@dataclass(frozen=True)
class CandidateMismatch:
    """One candidate's first failing criterion: (candidate, attribute, want, got)."""

    candidate: str
    attribute: str
    want: str
    got: str


class NoMatchingCandidateError(SelectionError):
    """No candidate matched the whole criteria spec.

    ``failures`` holds each candidate's first mismatch, in candidate order
    (empty when there were no candidates at all).
    """

    def __init__(self, failures: list[CandidateMismatch]) -> None:
        self.failures = failures
        super().__init__(f"no candidate matches all criteria ({len(failures)} examined)")


def criterion_matches(want: str, got: str) -> bool:
    """Whether observed state *got* satisfies the declared criterion *want*.

    ``>= N`` (numeric minimum) is the one comparator beyond equality — used by
    count-valued attributes; a non-numeric observation never satisfies it.
    """
    spec = want.strip()
    if spec.startswith(">="):
        try:
            return int(got) >= int(spec[2:].strip())
        except ValueError:
            return False
    return got == want


def validate_criteria[T](
    criteria: Mapping[str, str], vocabulary: Mapping[str, Callable[[T], str]]
) -> None:
    """Fail closed on criteria naming attributes outside *vocabulary*."""
    unknown = set(criteria) - set(vocabulary)
    if unknown:
        raise UnknownCriteriaError(sorted(unknown), sorted(vocabulary))


def first_mismatch[T](
    candidate: T,
    criteria: Mapping[str, str],
    vocabulary: Mapping[str, Callable[[T], str]],
) -> tuple[str, str, str] | None:
    """The first ``(attr, want, got)`` *candidate* fails on, or ``None`` on a full match.

    Criteria are evaluated in mapping order; ALL criteria belong to one
    atomic evaluation — a candidate matches only if every one holds.
    """
    for attr, want in criteria.items():
        got = vocabulary[attr](candidate)
        if not criterion_matches(want, got):
            return (attr, want, got)
    return None


def select_one[T](
    candidates: Sequence[T],
    criteria: Mapping[str, str],
    vocabulary: Mapping[str, Callable[[T], str]],
    *,
    describe: Callable[[T], str],
) -> T:
    """Resolve the ONE candidate matching the WHOLE criteria spec, atomically.

    Validates the criteria against the vocabulary first (fail closed), then
    binds the FIRST full match in *candidates* order — ordering, and therefore
    rerun determinism, is the caller's contract. On no match raises
    :class:`NoMatchingCandidateError` carrying each candidate's first
    mismatch, labelled via *describe*.
    """
    validate_criteria(criteria, vocabulary)
    failures: list[CandidateMismatch] = []
    for candidate in candidates:
        mismatch = first_mismatch(candidate, criteria, vocabulary)
        if mismatch is None:
            return candidate
        failures.append(CandidateMismatch(describe(candidate), *mismatch))
    raise NoMatchingCandidateError(failures)
