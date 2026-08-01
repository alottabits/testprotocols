"""Typed helpers shared by the testprotocols test suite.

``tests/`` is not a package, so pytest's default ``prepend`` import mode puts
this directory on ``sys.path`` and ``from _helpers import ...`` resolves. The
module name is kept unique across both packages' test directories because the
type checkers reject duplicate top-level module names.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, cast


def protocol_attrs(cls: type) -> frozenset[str]:
    """The members *cls* declares as a Protocol.

    ``__protocol_attrs__`` is a CPython 3.12 runtime detail that neither
    typeshed nor pyright models; Python 3.13's ``typing.get_protocol_members``
    supersedes it. Reaching it through one cast keeps that knowledge in a
    single place instead of a suppression on every conformance assertion.
    """
    return frozenset(cast("Any", cls).__protocol_attrs__)


def protocol_mro(cls: type) -> tuple[type, ...]:
    """*cls*'s method-resolution order.

    Declarative inheritance is what these tiering tests actually assert, but
    pyright does not model ``__mro__`` on a ``type[SomeProtocol]``; widening the
    operand to plain ``type`` restores it.
    """
    return cls.__mro__


def assert_str_value(member: StrEnum, expected: str) -> None:
    """Assert a StrEnum member itself compares equal to its wire string.

    Written as a helper because ``SomeEnum.MEMBER == "literal"`` inline trips
    the type checkers' strict-equality rule: both sides narrow to literal types
    they consider non-overlapping, even though a StrEnum member *is* a ``str``.
    Widening the operands to ``StrEnum`` and ``str`` restores the overlap while
    asserting exactly what the inline form asserted.
    """
    assert member == expected
