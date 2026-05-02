"""Tests for testoperations.sip_phone module."""

from __future__ import annotations

from unittest.mock import MagicMock

from testoperations.sip_phone import (
    call_a_phone,
    shutdown_phone,
)

# ---------------------------------------------------------------------------
# call_a_phone
# ---------------------------------------------------------------------------


class TestCallAPhone:
    def test_calls_off_hook_and_dial(self):
        caller = MagicMock()
        callee = MagicMock()
        callee.number = "2002"

        call_a_phone(caller, callee)

        caller.off_hook.assert_called_once_with()
        caller.dial.assert_called_once_with("2002")

    def test_dials_callee_number(self):
        caller = MagicMock()
        callee = MagicMock()
        callee.number = "3003"

        call_a_phone(caller, callee)
        caller.dial.assert_called_once_with("3003")


# ---------------------------------------------------------------------------
# shutdown_phone
# ---------------------------------------------------------------------------


class TestShutdownPhone:
    def test_calls_on_hook_and_kill(self):
        sip = MagicMock()

        shutdown_phone(sip)

        sip.on_hook.assert_called_once_with()
        sip.phone_kill.assert_called_once_with()
