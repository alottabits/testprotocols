"""PortRange and the released port grammar it replaces."""

from __future__ import annotations

import pytest
from testprotocols.models import PortRange, format_port_ranges, parse_port_ranges, port_tuple


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


def test_port_range_validates() -> None:
    for first, last in ((0, 5), (1, 65536), (9, 8)):
        with pytest.raises(ValueError):
            PortRange(first, last)
    bad: list[tuple[object, object]] = [(True, 5), (1.0, 5), (1, 5.0)]
    for pair in bad:
        with pytest.raises(TypeError, match=r"must be an int, not (bool|float)"):
            PortRange(*pair)  # type: ignore[arg-type]
    assert PortRange.single(80) == PortRange(80, 80)
    assert str(PortRange.single(80)) == "80" and str(PortRange(80, 90)) == "80-90"


@pytest.mark.parametrize("bad", ["80", b"80", (1, 2), ("80",), 80])
def test_port_tuple_refuses_what_is_not_a_tuple_of_port_ranges(bad: object) -> None:
    with pytest.raises(TypeError, match="PortRange"):
        port_tuple(bad)


def test_port_tuple_takes_a_list_as_a_tuple() -> None:
    assert port_tuple([PortRange.single(80)]) == (PortRange.single(80),)
