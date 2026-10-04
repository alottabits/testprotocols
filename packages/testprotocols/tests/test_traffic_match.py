"""TrafficMatch: what a rule selects, as a tagged union, and its released-pair converters."""

from __future__ import annotations

from typing import cast

import pytest
from testprotocols.models import (
    ApplicationCategory,
    ApplicationMatch,
    CategoryMatch,
    HostMatch,
    IpRangeMatch,
    L7MatchType,
    PortMatch,
    PortRange,
    TrafficMatch,
    match_fields,
    traffic_match,
)

_KINDS = [
    ("application", "zoom"),
    ("application_category", "video_streaming"),
    ("host", "www.example.com"),
    ("port", "8000-8100"),
    ("ip_range", "198.51.100.0/24"),
]


def _typed_matches() -> list[TrafficMatch]:
    return [
        ApplicationMatch("zoom"),
        CategoryMatch(ApplicationCategory.VIDEO_STREAMING),
        HostMatch("www.example.com"),
        PortMatch((PortRange(8000, 8100),)),
        IpRangeMatch("198.51.100.0/24"),
    ]


def test_traffic_match_round_trips_each_kind() -> None:
    for (kind, value), typed in zip(_KINDS, _typed_matches(), strict=True):
        assert traffic_match(L7MatchType(kind), value) == typed
        assert match_fields(typed) == (L7MatchType(kind), value)
        assert traffic_match(*match_fields(typed)) == typed
    port = traffic_match(L7MatchType.PORT, "22, 80-90")
    assert match_fields(port) == (L7MatchType.PORT, "22,80-90")  # canonical text


@pytest.mark.parametrize(
    ("kind", "value"),
    [
        (L7MatchType.APPLICATION_CATEGORY, "not_a_category"),
        (L7MatchType.PORT, "http"),
        (L7MatchType.APPLICATION, ""),
        (L7MatchType.HOST, ""),
        (L7MatchType.IP_RANGE, ""),
    ],
)
def test_traffic_match_refuses_a_bad_value(kind: L7MatchType, value: str) -> None:
    with pytest.raises(ValueError):
        traffic_match(kind, value)


def test_released_port_any_is_every_port() -> None:
    every = PortMatch((PortRange(1, 65535),))
    assert traffic_match(L7MatchType.PORT, "any") == every
    assert match_fields(every) == (L7MatchType.PORT, "1-65535")


def test_a_category_match_coerces_text_and_refuses_an_unknown_category() -> None:
    coerced = CategoryMatch("sports")  # type: ignore[arg-type]
    assert coerced.category is ApplicationCategory.SPORTS
    with pytest.raises(ValueError, match="bogus"):
        CategoryMatch("bogus")  # type: ignore[arg-type]


def test_an_address_range_match_takes_a_prefix_or_a_first_last_range() -> None:
    assert IpRangeMatch("198.51.100.10-198.51.100.20").cidr == "198.51.100.10-198.51.100.20"
    assert traffic_match(L7MatchType.IP_RANGE, "198.51.100.0/24") == IpRangeMatch("198.51.100.0/24")


def test_an_empty_match_is_refused() -> None:
    for build in (
        lambda: ApplicationMatch(""),
        lambda: HostMatch(""),
        lambda: IpRangeMatch(""),
        lambda: PortMatch(()),
    ):
        with pytest.raises(ValueError):
            build()


@pytest.mark.parametrize("bad", ["80", b"80", (1, 2), ("80",)])
def test_a_port_match_refuses_what_is_not_a_tuple_of_port_ranges(bad: object) -> None:
    with pytest.raises(TypeError, match="PortRange"):
        PortMatch(cast("tuple[PortRange, ...]", bad))
