"""Tests for the deprecation helpers used by renamed public symbols."""

from __future__ import annotations

import dataclasses
import warnings
from collections.abc import Callable
from enum import StrEnum
from typing import cast

import pytest
from testprotocols.deprecation import (
    coerce_enum,
    coerce_int,
    deprecated_attribute,
    renamed_attribute,
    warn_at_caller,
    warn_renamed,
)


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


def test_coerce_int_returns_an_int_unchanged_without_warning() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert coerce_int(443, what="port") == 443


def test_coerce_int_accepts_digits_and_warns() -> None:
    def boundary(value: str) -> int:
        return coerce_int(value, what="port")

    with pytest.warns(DeprecationWarning, match=r"port: .*'443'.*int") as caught:
        assert boundary("443") == 443
    assert caught[0].filename == __file__


def test_coerce_int_warning_points_at_the_calling_frame_with_skip_prefixes() -> None:
    def api(value: str) -> int:
        return coerce_int(value, what="port", skip_file_prefixes=("/nowhere",))

    with pytest.warns(DeprecationWarning) as caught:
        api("80")
    assert caught[0].filename == __file__


@pytest.mark.parametrize(("text", "number"), [("-1", -1), ("+5", 5), ("007", 7)])
def test_coerce_int_accepts_signed_decimal_text_and_warns(text: str, number: int) -> None:
    with pytest.warns(DeprecationWarning, match="deprecated"):
        assert coerce_int(text, what="vlan") == number


@pytest.mark.parametrize("text", ["http", "", " 80", "8 0", "1.5", "0x10", "\u0663"])
def test_coerce_int_rejects_non_numeric_text(text: str) -> None:
    with pytest.raises(ValueError, match=rf"port: {text!r} is not a decimal integer"):
        coerce_int(text, what="port")


def test_coerce_int_rejects_bool_and_float() -> None:
    for bad in (True, False, 1.5, None, b"1"):
        with pytest.raises(TypeError, match="port"):
            coerce_int(bad, what="port")  # type: ignore[arg-type]


def test_deprecated_attribute_warns_with_the_reason_and_returns_the_object() -> None:
    with pytest.warns(
        DeprecationWarning, match=r"pkg\.mod\.Orphan is deprecated; it has no successor"
    ):
        got = deprecated_attribute("pkg.mod", "Orphan", "it has no successor", {"Orphan": _New})
    assert got is _New


def test_deprecated_attribute_unknown_name_is_an_attribute_error() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(AttributeError, match=r"module 'pkg\.mod' has no attribute 'Nope'"):
            deprecated_attribute("pkg.mod", "Nope", "why", {"Orphan": _New})


def test_deprecated_attribute_points_at_the_accessing_module() -> None:
    def __getattr__(name: str) -> object:
        return deprecated_attribute("pkg.mod", name, "why", {"Orphan": _New})

    with pytest.warns(DeprecationWarning) as record:
        __getattr__("Orphan")
    assert record[0].filename == __file__


_MODEL_SOURCE = """
import dataclasses
from testprotocols.deprecation import coerce_enum


@dataclasses.dataclass(frozen=True)
class Painted:
    colour: object

    def __post_init__(self) -> None:
        coerce_enum(COLOUR, self.colour, what="colour", skip_file_prefixes=("/model/",))
"""


def _model_type() -> type:
    """A dataclass whose module file is ``/model/painted.py``, as a model in a package is."""
    namespace: dict[str, object] = {"COLOUR": _Colour, "__name__": __name__}
    exec(compile(_MODEL_SOURCE, "/model/painted.py", "exec"), namespace)
    return cast(type, namespace["Painted"])


def test_a_model_warning_points_at_the_construction_site_past_the_generated_init() -> None:
    painted = _model_type()
    with pytest.warns(DeprecationWarning) as caught:
        painted("red")
    assert caught[0].filename == __file__


def test_a_model_warning_points_at_the_replace_call_past_dataclasses() -> None:
    record = _model_type()(_Colour.RED)
    with pytest.warns(DeprecationWarning) as caught:
        dataclasses.replace(record, colour="blue")
    assert caught[0].filename == __file__


def test_warn_at_caller_skips_callers_after_the_skipped_frames() -> None:
    namespace: dict[str, object] = {"warn_at_caller": warn_at_caller}
    source = "def boundary():\n    warn_at_caller('gone', callers=1)\n"
    exec(compile(source, "/driver/boundary.py", "exec"), namespace)
    boundary = cast("Callable[[], None]", namespace["boundary"])
    with pytest.warns(DeprecationWarning, match="gone") as caught:
        boundary()
    assert caught[0].filename == __file__
