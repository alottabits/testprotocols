"""SIP phone operations — multi-step call sequences.

Receives resolved ``sip_phone`` template instances from the caller.
Thin wrappers (answer, disconnect, hold, etc.) are deleted — step definitions
call the template method directly.
"""

from __future__ import annotations

from typing import Any

from testprotocols.sip_phone import SipPhone


def call_a_phone(caller: SipPhone, callee: Any) -> None:
    """Initiate a call. *caller* and *callee* are SipPhone template instances.

    Takes the caller off-hook and dials the callee's SIP phone number.

    *callee* is typed ``Any`` because the function reads ``callee.number``,
    which is not part of the :class:`SipPhone` protocol surface.
    """
    caller.off_hook()
    caller.dial(callee.number)


def shutdown_phone(sip_phone: SipPhone) -> None:
    """Put on-hook and stop the SIP phone application."""
    sip_phone.on_hook()
    sip_phone.phone_kill()
