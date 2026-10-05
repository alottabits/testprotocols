"""The parsers of the released text forms: ports and iperf window sizes."""

from __future__ import annotations

import pytest
from testoperations._compat import parse_window_size
from testoperations.pairs import parse_nat_port_ranges, parse_port_ranges
from testprotocols.models import PortRange


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


@pytest.mark.parametrize(
    ("text", "size"),
    [
        ("8M", 8 * 1024 * 1024),
        ("8m", 8 * 1024 * 1024),
        ("512K", 512 * 1024),
        ("1G", 1024**3),
        ("1.5M", 1572864),
        ("65536", 65536),
        (" 2M ", 2 * 1024 * 1024),
    ],
)
def test_parse_window_size_uses_iperf_binary_units(text: str, size: int) -> None:
    assert parse_window_size(text) == size


@pytest.mark.parametrize("text", ["", "8MB", "M", "-1M", "0", "eight"])
def test_parse_window_size_refuses_malformed_text(text: str) -> None:
    with pytest.raises(ValueError):
        parse_window_size(text)


def test_parse_window_size_refuses_a_non_text() -> None:
    with pytest.raises(TypeError):
        parse_window_size(8)  # type: ignore[arg-type]  # the non-text argument is the check
