"""The parsers and formatters of the released text forms: ports and traffic matches."""

from __future__ import annotations

import pytest
from testoperations._compat import (
    format_port_ranges,
    match_fields,
    parse_nat_port_ranges,
    parse_port_ranges,
    port_tuple,
    traffic_match,
)
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
)


@pytest.mark.parametrize("text", ["any", "80", "80-90", "22,80-90"])
def test_parse_and_format_port_ranges_round_trip(text: str) -> None:
    assert format_port_ranges(parse_port_ranges(text)) == text


def test_parse_port_ranges_values() -> None:
    assert parse_port_ranges("any") == ()
    assert parse_port_ranges("22, 80-90") == (PortRange.single(22), PortRange(80, 90))


@pytest.mark.parametrize("text", ["90-80", "0", "65536", "http", "", "80,", "-80", "1-2-3", "+80"])
def test_parse_port_ranges_rejects_a_malformed_spec(text: str) -> None:
    with pytest.raises(ValueError, match="malformed port spec"):
        parse_port_ranges(text)


def test_the_nat_text_for_no_port_is_empty() -> None:
    assert parse_nat_port_ranges("") == ()
    assert parse_nat_port_ranges("any") == ()
    assert parse_nat_port_ranges("80") == (PortRange.single(80),)


@pytest.mark.parametrize("bad", ["80", b"80", (1, 2), ("80",), 80])
def test_port_tuple_refuses_what_is_not_a_tuple_of_port_ranges(bad: object) -> None:
    with pytest.raises(TypeError, match="PortRange"):
        port_tuple(bad)


def test_port_tuple_takes_a_list_as_a_tuple() -> None:
    assert port_tuple([PortRange.single(80)]) == (PortRange.single(80),)


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


def test_an_address_range_match_takes_a_prefix_or_a_first_last_range() -> None:
    assert traffic_match(L7MatchType.IP_RANGE, "198.51.100.0/24") == IpRangeMatch("198.51.100.0/24")
    ranged = traffic_match(L7MatchType.IP_RANGE, "198.51.100.10-198.51.100.20")
    assert ranged == IpRangeMatch("198.51.100.10-198.51.100.20")
