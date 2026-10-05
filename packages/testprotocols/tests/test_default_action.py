"""DefaultAction: what traffic no rule decides gets; a driver converts a plain string once."""

from __future__ import annotations

import warnings

import pytest
from testprotocols.models import DefaultAction


def test_default_action_values() -> None:
    assert [a.value for a in DefaultAction] == ["accept", "drop", "reject"]


def _boundary(action: DefaultAction | str) -> DefaultAction:
    """A minimal driver member: it converts the action once, at its boundary."""
    return DefaultAction(action)


def test_a_driver_that_converts_at_the_boundary_rejects_an_unknown_action() -> None:
    with pytest.raises(ValueError, match="'allow'"):
        _boundary("allow")


def test_a_driver_that_converts_at_the_boundary_takes_either_form_silently() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert _boundary("drop") is DefaultAction.DROP
        assert _boundary(DefaultAction.ACCEPT) is DefaultAction.ACCEPT
