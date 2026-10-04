"""DefaultAction: what traffic no rule decides gets; a driver coerces a plain string once."""

from __future__ import annotations

import warnings

import pytest
from testprotocols.deprecation import coerce_enum
from testprotocols.models import DefaultAction


def test_default_action_values() -> None:
    assert [a.value for a in DefaultAction] == ["accept", "drop", "reject"]


def _boundary(action: DefaultAction | str) -> DefaultAction:
    """A minimal driver member: it coerces the action once, at its boundary."""
    return coerce_enum(DefaultAction, action, what="set_policy action")


def test_a_driver_that_coerces_at_the_boundary_rejects_an_unknown_action() -> None:
    with pytest.raises(
        ValueError,
        match=r"set_policy action: 'allow' is not one of \['accept', 'drop', 'reject'\]",
    ):
        _boundary("allow")


def test_a_driver_that_coerces_at_the_boundary_warns_at_its_caller() -> None:
    with pytest.warns(DeprecationWarning) as caught:
        assert _boundary("drop") is DefaultAction.DROP
    assert caught[0].filename == __file__
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert _boundary(DefaultAction.ACCEPT) is DefaultAction.ACCEPT
