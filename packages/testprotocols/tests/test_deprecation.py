"""Tests for the deprecation helpers used by renamed public symbols."""

from __future__ import annotations

import warnings
from enum import StrEnum

import pytest
from testprotocols.deprecation import coerce_enum, renamed_attribute, warn_renamed


class _New:
    pass


def test_renamed_attribute_warns_and_returns_the_new_object() -> None:
    with pytest.warns(DeprecationWarning, match=r"pkg\.mod\.Old is deprecated; use New"):
        got = renamed_attribute("pkg.mod", "Old", {"Old": "New"}, {"New": _New})
    assert got is _New


def test_renamed_attribute_unknown_name_is_an_attribute_error() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(AttributeError, match=r"module 'pkg\.mod' has no attribute 'Nope'"):
            renamed_attribute("pkg.mod", "Nope", {"Old": "New"}, {"New": _New})


def test_warn_renamed_names_both_members() -> None:
    with pytest.warns(DeprecationWarning, match=r"old_name is deprecated; use new_name"):
        warn_renamed("old_name", "new_name")


class _Colour(StrEnum):
    RED = "red"
    BLUE = "blue"


def test_coerce_enum_returns_a_member_unchanged_without_warning() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert coerce_enum(_Colour, _Colour.RED, what="colour") is _Colour.RED


def test_coerce_enum_accepts_a_member_value_and_warns() -> None:
    with pytest.warns(DeprecationWarning, match=r"colour: .*'red'.*_Colour\.RED"):
        assert coerce_enum(_Colour, "red", what="colour") is _Colour.RED


def test_coerce_enum_rejects_an_unknown_value() -> None:
    with pytest.raises(ValueError, match=r"colour: 'green' is not one of \['red', 'blue'\]"):
        coerce_enum(_Colour, "green", what="colour")


def test_coerce_enum_warning_points_at_the_calling_frame_with_skip_prefixes() -> None:
    def api(value: str) -> _Colour:
        return coerce_enum(_Colour, value, what="colour", skip_file_prefixes=("/nowhere",))

    with pytest.warns(DeprecationWarning) as caught:
        api("blue")
    assert caught[0].filename == __file__


def test_coerce_enum_direct_warning_points_at_the_callers_caller() -> None:
    def boundary(value: str) -> _Colour:
        return coerce_enum(_Colour, value, what="colour")

    with pytest.warns(DeprecationWarning) as caught:
        boundary("red")
    assert caught[0].filename == __file__
