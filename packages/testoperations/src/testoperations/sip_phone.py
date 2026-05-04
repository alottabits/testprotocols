"""SIP phone operations — multi-step call sequences.

Receives resolved ``sip_phone`` template instances from the caller.
Thin wrappers (answer, disconnect, hold, etc.) are deleted — step definitions
call the template method directly.
"""

from __future__ import annotations

from testprotocols.devices.voice import SipPhoneDevice
from testprotocols.sip_phone import SipPhone


def call_a_phone(caller: SipPhone, callee: SipPhoneDevice) -> None:
    """Initiate a call from *caller* to *callee*.

    Takes the caller off-hook and dials the callee's SIP phone number.
    *callee* is a :class:`SipPhoneDevice` archetype — its ``number`` attribute
    carries the dial-string identifier of the destination phone.
    """
    caller.off_hook()
    caller.dial(callee.number)


def shutdown_phone(sip_phone: SipPhone) -> None:
    """Put on-hook and stop the SIP phone application."""
    sip_phone.on_hook()
    sip_phone.phone_kill()
