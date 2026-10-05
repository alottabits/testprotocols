"""Importing ``testprotocols`` and building its records never warns.

A deprecation is stated (docstring, ``@deprecated(..., category=None)``, CHANGELOG), never
implemented at run time: no module warns on import and no record warns on construction.
The imports run in a fresh interpreter, because this session has imported the package
already. Every exported record is built from minimal released-style values: a plain
string for an ``E | str`` field, the text form of a text/typed pair, nothing else.
The ``@deprecated`` classes are built too: their marker passes ``category=None``.
"""

from __future__ import annotations

import dataclasses
import enum
import inspect
import pkgutil
import subprocess
import sys
import types
import typing
import warnings
from collections import abc
from datetime import UTC, date, datetime, time, timedelta
from ipaddress import (
    IPv4Address,
    IPv4Interface,
    IPv4Network,
    IPv6Address,
    IPv6Interface,
    IPv6Network,
)

import pytest
import testprotocols
from testprotocols import models

_SIMPLE: dict[object, object] = {
    str: "x",
    int: 1,
    float: 1.0,
    bool: False,
    bytes: b"",
    object: "x",
    datetime: datetime(2026, 1, 1, tzinfo=UTC),
    date: date(2026, 1, 1),
    time: time(0, 0),
    timedelta: timedelta(seconds=1),
    IPv4Address: IPv4Address("192.0.2.1"),
    IPv6Address: IPv6Address("2001:db8::1"),
    IPv4Network: IPv4Network("192.0.2.0/24"),
    IPv6Network: IPv6Network("2001:db8::/64"),
    IPv4Interface: IPv4Interface("192.0.2.1/24"),
    IPv6Interface: IPv6Interface("2001:db8::1/64"),
}


def _value(hint: object) -> object:
    """A minimal released-style value for *hint*."""
    origin = typing.get_origin(hint)
    if origin is typing.Union or origin is types.UnionType:
        args = typing.get_args(hint)
        if str in args:  # ``E | str``, ``str | None``: the plain released text
            return "x"
        if type(None) in args:
            return None
        return _value(args[0])
    if origin is typing.Literal:
        return typing.get_args(hint)[0]
    if origin is typing.Annotated:
        return _value(typing.get_args(hint)[0])
    if origin is list:
        return []
    if origin in (set, frozenset):
        return frozenset[object]()
    if origin in (tuple, abc.Sequence):
        return ()
    if origin in (dict, abc.Mapping):
        return {}
    if hint in _SIMPLE:
        return _SIMPLE[hint]
    if isinstance(hint, type) and issubclass(hint, enum.Enum):
        return next(iter(hint))
    if isinstance(hint, type) and dataclasses.is_dataclass(hint):
        return _build(hint)
    if isinstance(hint, type) and _is_namedtuple(hint):
        return _build(hint)
    raise AssertionError(f"no minimal value for {hint!r}")


def _is_namedtuple(cls: type) -> bool:
    return tuple in cls.__mro__ and hasattr(cls, "_fields")


def _namedtuple_required(cls: type) -> list[str]:
    fields: tuple[str, ...] = getattr(cls, "_fields")
    defaults: dict[str, object] = getattr(cls, "_field_defaults")
    return [f for f in fields if f not in defaults]


def _build(cls: type) -> object:
    """An instance of *cls* with every required field given a minimal value."""
    hints = typing.get_type_hints(cls)
    if _is_namedtuple(cls):
        return cls(**{f: _value(hints[f]) for f in _namedtuple_required(cls)})
    kwargs: dict[str, object] = {}
    for field in dataclasses.fields(cls):
        if not field.init:
            continue
        no_default = (
            field.default is dataclasses.MISSING and field.default_factory is dataclasses.MISSING
        )
        if no_default:
            kwargs[field.name] = _value(hints[field.name])
    return cls(**kwargs)


def _records() -> list[type]:
    names = getattr(models, "__all__", None) or [n for n in dir(models) if not n.startswith("_")]
    found: list[type] = []
    for name in names:
        obj = getattr(models, name)
        if inspect.isclass(obj) and (dataclasses.is_dataclass(obj) or _is_namedtuple(obj)):
            found.append(obj)
    return found


def _modules() -> list[str]:
    return sorted(
        info.name for info in pkgutil.walk_packages(testprotocols.__path__, prefix="testprotocols.")
    )


def test_importing_every_module_never_warns() -> None:
    modules = _modules()
    assert "testprotocols.models.firewall" in modules
    code = "import importlib, sys\nfor m in sys.argv[1:]:\n    importlib.import_module(m)\n"
    result = subprocess.run(
        [sys.executable, "-W", "error", "-c", code, "testprotocols", *modules],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""


def test_the_records_are_found() -> None:
    records = _records()
    assert {models.FirewallRule, models.SecurityEvent, models.PortRange} <= set(records)
    assert len(records) > 50


@pytest.mark.parametrize("cls", _records(), ids=lambda c: c.__name__)
def test_building_a_record_never_warns(cls: type) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        instance = _build(cls)
    assert isinstance(instance, cls)
