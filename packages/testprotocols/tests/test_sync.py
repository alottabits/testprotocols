"""The synced-field rule (shape 4(ii)): a deprecated text field and its typed successor agree.

Tested on small toy records, so the rule is pinned independently of any one contract
model: :class:`_Ported` has two :class:`SyncedField` port pairs (text ``"any"``, ``"80"``,
``"80-90"``, ``"22,80-90"`` against ``tuple[PortRange, ...]``), and :class:`_Selector`
has one :class:`SyncedFields` pair (the ``(match_type, value)`` text spelling a
:data:`TrafficMatch`).
"""

from __future__ import annotations

import dataclasses
import typing
import warnings
from dataclasses import dataclass, field, fields, replace
from typing import override

import pytest
from testprotocols.models import (
    ApplicationMatch,
    CategoryMatch,
    HostMatch,
    L7MatchType,
    PortMatch,
    PortRange,
    TrafficMatch,
    format_port_ranges,
    match_fields,
    parse_port_ranges,
    port_tuple,
    traffic_match,
)
from testprotocols.models._sync import SyncedField, SyncedFields, assign, settle

# --- a toy record with two SyncedField pairs ---

_PORT_PAIRS = tuple(
    SyncedField[tuple[PortRange, ...]](
        old, new, parse_port_ranges, format_port_ranges, port_tuple, "any"
    )
    for old, new in (("src_port", "src_ports"), ("dst_port", "dst_ports"))
)


@dataclass
class _Ported:
    name: str = "r"
    src_port: str = "any"
    dst_port: str = "any"
    comment: str = ""
    src_ports: tuple[PortRange, ...] = field(default=(), kw_only=True)
    dst_ports: tuple[PortRange, ...] = field(default=(), kw_only=True)
    _ports_seen: tuple[str, ...] | None = field(
        default=None, kw_only=True, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        settle(self, _PORT_PAIRS, "_ports_seen")

    @override
    def __setattr__(self, name: str, value: object) -> None:
        assign(self, name, value, _PORT_PAIRS, "_ports_seen")


def _ranged() -> _Ported:
    return _Ported(dst_ports=(PortRange(80, 90),))


def test_new_field_is_visible_through_the_old_field() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        record = _Ported(
            dst_ports=(PortRange(80, 90),),
            src_ports=(PortRange.single(22), PortRange(80, 90)),
        )
    assert record.dst_port == "80-90"
    assert record.src_port == "22,80-90"
    assert _Ported().dst_port == "any"


def test_old_field_warns_and_still_works() -> None:
    with pytest.warns(DeprecationWarning, match=r"_Ported\.dst_port is deprecated; use dst_ports"):
        record = _Ported(dst_port="80-90")
    assert record.dst_ports == (PortRange(80, 90),)
    assert record.dst_port == "80-90"
    assert record.src_ports == ()


def test_old_field_warning_points_at_the_construction_site() -> None:
    with pytest.warns(DeprecationWarning) as caught:
        _Ported(src_port="22")
    assert caught[0].filename == __file__


def test_consistent_old_and_new_ports_do_not_warn() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        record = _Ported(dst_port="80", dst_ports=(PortRange(80, 80),))
    assert record.dst_ports == (PortRange(80, 80),)


def test_conflicting_old_and_new_ports_raise() -> None:
    with pytest.raises(ValueError, match="disagree"):
        _Ported(dst_port="80", dst_ports=(PortRange(443, 443),))


def test_malformed_old_port_raises() -> None:
    with pytest.raises(ValueError):
        _Ported(src_port="http")


def test_old_text_is_normalised_to_its_canonical_twin() -> None:
    with pytest.warns(DeprecationWarning):
        loose = _Ported(dst_port="22, 80-90")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        tight = _Ported(dst_ports=(PortRange.single(22), PortRange(80, 90)))
        agreed = _Ported(
            dst_port="22, 80-90",
            dst_ports=(PortRange.single(22), PortRange(80, 90)),
        )
    assert loose.dst_port == "22,80-90" and loose == tight == agreed


def test_replace_with_the_old_field_any_clears_the_ports() -> None:
    with pytest.warns(DeprecationWarning, match="dst_port is deprecated"):
        cleared = replace(_ranged(), dst_port="any")
    assert cleared.dst_ports == () and cleared.dst_port == "any"


def test_replace_with_the_old_field_changes_the_ports_and_warns() -> None:
    with pytest.warns(DeprecationWarning):
        moved = replace(_ranged(), dst_port="443")
    assert moved.dst_ports == (PortRange.single(443),) and moved.dst_port == "443"


def test_replace_with_the_new_field_updates_the_text_without_warning() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        moved = replace(_ranged(), dst_ports=(PortRange.single(443),))
        cleared = replace(_ranged(), dst_ports=())
        kept = replace(_ranged(), comment="x")
    assert moved.dst_port == "443" and cleared.dst_port == "any"
    assert kept.dst_port == "80-90" and kept.dst_ports == _ranged().dst_ports


def test_replace_with_both_ports_fields_must_agree() -> None:
    with pytest.raises(ValueError, match="disagree"):
        replace(_ranged(), dst_port="443", dst_ports=(PortRange(1, 2),))


def test_assigning_the_new_field_updates_the_text() -> None:
    record = _ranged()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        record.dst_ports = (PortRange.single(443),)
    assert record.dst_port == "443"


def test_assigning_the_old_field_reparses_and_warns() -> None:
    record = _ranged()
    with pytest.warns(DeprecationWarning):
        record.dst_port = "443"
    ports: tuple[object, ...] = record.dst_ports  # widened: mypy would narrow it to one item
    assert ports == (PortRange.single(443),)
    with pytest.warns(DeprecationWarning):
        record.dst_port = "any"
    ports = record.dst_ports
    assert not ports
    with pytest.raises(ValueError):
        record.dst_port = "http"
    ports = record.dst_ports
    assert not ports and record.dst_port == "any"  # a refused value changes nothing


def test_assigning_the_old_field_a_non_text_raises_type_error_and_changes_nothing() -> None:
    record = _ranged()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(TypeError, match=r"_Ported\.dst_port takes text"):
            record.dst_port = 443  # type: ignore[assignment]
    assert record == _ranged() and record.dst_port == "80-90"


def test_a_malformed_old_text_is_parsed_before_it_warns() -> None:
    record = _ranged()
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # a warning before the parse would raise here
        with pytest.raises(ValueError, match="malformed port spec"):
            record.dst_port = "http"
        with pytest.raises(ValueError, match="malformed port spec"):
            replace(record, dst_port="http")
    assert record == _ranged()


def test_the_provenance_field_is_hidden() -> None:
    assert "_ports_seen" not in repr(_ranged())
    assert "_ports_seen" not in {f.name for f in fields(_Ported) if f.repr}
    assert "_ports_seen" not in {f.name for f in fields(_Ported) if f.compare}


def test_deprecation_warning_points_at_the_caller_on_every_path() -> None:
    with pytest.warns(DeprecationWarning) as built:
        _Ported(src_port="22")
    with pytest.warns(DeprecationWarning) as replaced:
        replace(_ranged(), dst_port="22")
    record = _ranged()
    with pytest.warns(DeprecationWarning) as assigned:
        record.dst_port = "22"
    for caught in (built, replaced, assigned):
        assert caught[0].filename == __file__


def test_a_misordered_provenance_field_is_refused() -> None:
    pairs = (
        SyncedField[tuple[int, ...]](
            "text",
            "typed",
            lambda t: tuple(map(int, t.split(","))) if t != "-" else (),
            lambda v: ",".join(map(str, v)) or "-",
            tuple,
            "-",
        ),
    )

    @dataclass
    class Misordered:
        seen: tuple[str, ...] | None = field(default=None, repr=False, compare=False)
        text: str = "-"
        typed: tuple[int, ...] = ()

        def __post_init__(self) -> None:
            settle(self, pairs, "seen")

        @override
        def __setattr__(self, name: str, value: object) -> None:
            assign(self, name, value, pairs, "seen")

    with pytest.raises(TypeError, match=r"Misordered.*last field"):
        Misordered()


def test_pseudo_fields_after_the_provenance_field_are_not_fields() -> None:
    pairs = (SyncedField[int]("text", "typed", int, str, int, "0"),)

    @dataclass
    class Tidy:
        text: str = "0"
        typed: int = 0
        seen: tuple[str, ...] | None = field(default=None, repr=False, compare=False)
        marker: typing.ClassVar[int] = 1  # after the provenance field, but not a field
        hint: dataclasses.InitVar[int] = 0  # likewise

        def __post_init__(self, hint: int) -> None:
            settle(self, pairs, "seen")

        @override
        def __setattr__(self, name: str, value: object) -> None:
            assign(self, name, value, pairs, "seen")

    assert Tidy(typed=5).text == "5"


def test_an_undecorated_subclass_of_a_synced_model_is_refused_by_name() -> None:
    class Loose(_Ported):  # not re-decorated with @dataclass
        extra: int = 1

    with pytest.raises(TypeError, match=r"Loose.*@dataclass"):
        Loose()


@pytest.mark.parametrize("bad", ["80", b"80", (1, 2), ("80",)])
def test_the_typed_side_refuses_what_its_normalizer_refuses(bad: object) -> None:
    with pytest.raises(TypeError, match="PortRange"):
        _Ported(dst_ports=bad)  # type: ignore[arg-type]
    record = _ranged()
    with pytest.raises(TypeError):
        record.dst_ports = bad  # type: ignore[assignment]
    assert record.dst_port == "80-90" and record == _ranged()  # a refused value changes nothing


def test_the_typed_side_is_normalized() -> None:
    record = _Ported(dst_ports=[PortRange.single(80)])  # type: ignore[arg-type]
    assert record.dst_ports == (PortRange.single(80),) and record.dst_port == "80"


# --- a toy record with one SyncedFields pair: (match_type, value) spells a TrafficMatch ---

_NO_MATCH = (L7MatchType.APPLICATION, "")


def _match_text(match: TrafficMatch | None) -> tuple[L7MatchType, str]:
    return _NO_MATCH if match is None else match_fields(match)


def _match_of(text: tuple[L7MatchType, str]) -> TrafficMatch | None:
    return traffic_match(*text)


def _same(match: TrafficMatch | None) -> TrafficMatch | None:
    return match


_MATCH_PAIRS = (
    SyncedFields[tuple[L7MatchType, str], TrafficMatch | None](
        ("match_type", "value"),
        (L7MatchType, str),
        "match",
        _match_of,
        _match_text,
        _same,
        _NO_MATCH,
    ),
)


@dataclass
class _Selector:
    name: str = "s"
    match_type: L7MatchType = L7MatchType.APPLICATION
    value: str = ""
    match: TrafficMatch | None = field(default=None, kw_only=True)
    _match_seen: tuple[tuple[L7MatchType, str], ...] | None = field(
        default=None, kw_only=True, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        settle(self, _MATCH_PAIRS, "_match_seen")

    @override
    def __setattr__(self, name: str, value: object) -> None:
        assign(self, name, value, _MATCH_PAIRS, "_match_seen")


def test_fields_new_side_is_visible_through_the_old_fields() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        record = _Selector(match=HostMatch("www.example.com"))
        assert (record.match_type, record.value) == (L7MatchType.HOST, "www.example.com")
        moved = replace(record, match=PortMatch((PortRange.single(443),)))
        record.match = PortMatch((PortRange.single(22), PortRange(80, 90)))
        kept = replace(record)
    assert (moved.match_type, moved.value) == (L7MatchType.PORT, "443")
    assert (record.match_type, record.value) == (L7MatchType.PORT, "22,80-90")
    assert kept == record and kept.match == record.match


def test_fields_old_side_warns_and_the_side_that_changed_wins() -> None:
    with pytest.warns(DeprecationWarning, match=r"_Selector\.match_type/value is deprecated"):
        record = _Selector(match_type=L7MatchType.HOST, value="www.example.com")
    assert record.match == HostMatch("www.example.com")
    with pytest.warns(DeprecationWarning):
        record.value = "cdn.example.com"
    assert record.match == HostMatch("cdn.example.com")
    with pytest.warns(DeprecationWarning):
        swapped = replace(record, match_type=L7MatchType.PORT, value="443")
    assert swapped.match == PortMatch((PortRange.single(443),))
    with pytest.warns(DeprecationWarning):
        renamed = replace(_Selector(match=ApplicationMatch("conference")), value="chat")
    assert renamed.match == ApplicationMatch("chat")
    with pytest.warns(DeprecationWarning):
        record.match_type = L7MatchType.APPLICATION
    assert record.match is not None
    assert match_fields(record.match) == (L7MatchType.APPLICATION, "cdn.example.com")


def test_fields_consistent_sides_do_not_warn_and_conflicts_raise() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        record = _Selector(match_type=L7MatchType.HOST, value="h", match=HostMatch("h"))
    assert record.match == HostMatch("h")
    with pytest.raises(ValueError, match="disagree"):
        _Selector(match_type=L7MatchType.HOST, value="h", match=HostMatch("x"))
    with pytest.raises(ValueError, match="disagree"):
        replace(record, value="y", match=HostMatch("z"))


def test_fields_a_bad_old_value_is_parsed_before_it_warns_and_changes_nothing() -> None:
    from testprotocols.models import ApplicationCategory

    with pytest.raises(ValueError):
        _Selector(match_type=L7MatchType.APPLICATION_CATEGORY, value="not_a_category")
    record = _Selector(match=CategoryMatch(ApplicationCategory.SPORTS))
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # parsed before it warns
        with pytest.raises(ValueError):
            record.value = "not_a_category"
        with pytest.raises(ValueError):
            replace(record, match_type=L7MatchType.PORT)  # "sports" is no port
    assert record.match == CategoryMatch(ApplicationCategory.SPORTS)
    assert (record.match_type, record.value) == (L7MatchType.APPLICATION_CATEGORY, "sports")


def test_fields_warning_points_at_the_caller_and_provenance_is_hidden() -> None:
    with pytest.warns(DeprecationWarning) as built:
        record = _Selector(match_type=L7MatchType.HOST, value="h")
    with pytest.warns(DeprecationWarning) as replaced:
        replace(record, value="x")
    with pytest.warns(DeprecationWarning) as assigned:
        record.value = "y"
    for caught in (built, replaced, assigned):
        assert caught[0].filename == __file__
    shown = repr(_Selector(match=HostMatch("h")))
    assert "_seen" not in shown and "match=HostMatch(host='h')" in shown


def test_fields_assigning_an_old_field_a_wrong_type_raises() -> None:
    record = _Selector(match=HostMatch("h"))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(TypeError, match="value takes str"):
            record.value = 443  # type: ignore[assignment]
        with pytest.raises(TypeError, match="match_type takes L7MatchType"):
            record.match_type = 5  # type: ignore[assignment]
        legal = r"^_Selector\.match_type: 'bogus' is not one of \['application', "
        with pytest.raises(ValueError, match=legal):
            record.match_type = "bogus"  # type: ignore[assignment]
    assert record.match == HostMatch("h") and record.value == "h"


def test_fields_a_plain_string_for_an_enum_field_converts_and_warns() -> None:
    record = _Selector(match=ApplicationMatch("www.example.com"))
    with pytest.warns(DeprecationWarning) as caught:
        record.match_type = "host"  # type: ignore[assignment]
    assert record.match_type is L7MatchType.HOST
    assert [str(w.message) for w in caught] == [
        "_Selector.match_type: plain string 'host' is deprecated; pass L7MatchType.HOST",
        "_Selector.match_type/value is deprecated; use match",
    ]
    assert all(w.filename == __file__ for w in caught)
    assert record.match == HostMatch("www.example.com")
