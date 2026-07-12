"""Tests for testoperations.selection (criteria-driven candidate selection)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from testoperations.selection import (
    CandidateMismatch,
    NoMatchingCandidateError,
    UnknownCriteriaError,
    criterion_matches,
    first_mismatch,
    select_one,
    validate_criteria,
)


@dataclass(frozen=True)
class Site:
    name: str
    color: str
    clients: int


VOCAB = {
    "color": lambda s: s.color,
    "clients": lambda s: str(s.clients),
}

RED2 = Site("ams", "red", 2)
BLUE1 = Site("rot", "blue", 1)
RED0 = Site("erm", "red", 0)


@pytest.mark.parametrize(
    ("want", "got", "expected"),
    [
        ("red", "red", True),
        ("red", "blue", False),
        (">= 2", "2", True),
        (">= 2", "3", True),
        (">=2", "1", False),
        (">= 2", "many", False),  # non-numeric observation never satisfies >=
    ],
)
def test_criterion_matches(want: str, got: str, expected: bool) -> None:
    assert criterion_matches(want, got) is expected


def test_validate_criteria_accepts_known() -> None:
    validate_criteria({"color": "red"}, VOCAB)  # no raise


def test_validate_criteria_fails_closed_on_unknown() -> None:
    with pytest.raises(UnknownCriteriaError) as exc:
        validate_criteria({"color": "red", "zone": "a", "band": "b"}, VOCAB)
    assert exc.value.unknown == ["band", "zone"]
    assert exc.value.known == ["clients", "color"]


def test_first_mismatch_none_on_full_match() -> None:
    assert first_mismatch(RED2, {"color": "red", "clients": ">= 2"}, VOCAB) is None


def test_first_mismatch_reports_first_failure_in_criteria_order() -> None:
    assert first_mismatch(BLUE1, {"color": "red", "clients": ">= 2"}, VOCAB) == (
        "color",
        "red",
        "blue",
    )


def test_select_one_first_full_match_in_caller_order_binds() -> None:
    assert (
        select_one([BLUE1, RED2, RED0], {"color": "red"}, VOCAB, describe=lambda s: s.name) is RED2
    )


def test_select_one_validates_criteria_first() -> None:
    with pytest.raises(UnknownCriteriaError):
        select_one([RED2], {"zone": "a"}, VOCAB, describe=lambda s: s.name)


def test_select_one_no_match_carries_per_candidate_failures() -> None:
    with pytest.raises(NoMatchingCandidateError) as exc:
        select_one(
            [BLUE1, RED0], {"color": "red", "clients": ">= 2"}, VOCAB, describe=lambda s: s.name
        )
    assert exc.value.failures == [
        CandidateMismatch("rot", "color", "red", "blue"),
        CandidateMismatch("erm", "clients", ">= 2", "0"),
    ]


def test_select_one_empty_candidates_raises_with_no_failures() -> None:
    with pytest.raises(NoMatchingCandidateError) as exc:
        select_one([], {"color": "red"}, VOCAB, describe=lambda s: s.name)
    assert exc.value.failures == []
