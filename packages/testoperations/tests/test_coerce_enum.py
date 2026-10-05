"""coerce_enum: an operation's released string parameter, converted to its enum."""

from __future__ import annotations

import warnings
from enum import IntEnum, StrEnum
from typing import cast

import pytest
from testoperations._compat import coerce_enum


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


@pytest.mark.parametrize("value", [None, b"red", 1.0, ["red"], True, 5])
def test_coerce_enum_rejects_a_value_of_the_wrong_type_with_type_error(value: object) -> None:
    with pytest.raises(TypeError, match=r"colour: takes a _Colour or str, not "):
        coerce_enum(_Colour, cast("_Colour | str", value), what="colour")


class _Width(IntEnum):
    NARROW = 20
    WIDE = 80


@pytest.mark.parametrize("value", [None, b"80", 80.0, [80], True])
def test_coerce_enum_rejects_the_wrong_type_for_an_int_enum_with_type_error(
    value: object,
) -> None:
    with pytest.raises(TypeError, match=r"width: takes a _Width, int or str, not "):
        coerce_enum(_Width, cast("_Width | int", value), what="width")


@pytest.mark.parametrize("value", [40, "80", "wide"])
def test_coerce_enum_keeps_value_error_for_an_int_enum_value_naming_no_member(
    value: int | str,
) -> None:
    with pytest.raises(ValueError, match=r"width: .* is not one of \[20, 80\]"):
        coerce_enum(_Width, value, what="width")


def test_coerce_enum_int_enum_number_returns_the_member_without_warning() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert coerce_enum(_Width, 80, what="width") is _Width.WIDE


def test_coerce_enum_warning_points_at_the_operations_caller() -> None:
    def operation(value: str) -> _Colour:
        return coerce_enum(_Colour, value, what="colour")

    with pytest.warns(DeprecationWarning) as caught:
        operation("red")
    assert caught[0].filename == __file__
