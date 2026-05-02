"""Voice / SipPhone template.

Defines the abstract contract for SIP phone operations including call
state management, dialling, and feature codes.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SipPhone(Protocol):
    """Abstract contract for SIP phone operations."""

    def phone_start(self) -> None:
        """Start the SIP phone software."""
        ...

    def phone_config(self, ipv6_flag: bool, sipserver_fqdn: str = "") -> None:
        """Configure the SIP phone with the given server FQDN and IP-version flag."""
        ...

    def phone_kill(self) -> None:
        """Terminate the SIP phone software."""
        ...

    def on_hook(self) -> None:
        """Place the phone on-hook (hang up)."""
        ...

    def off_hook(self) -> None:
        """Take the phone off-hook."""
        ...

    def answer(self) -> bool:
        """Answer an incoming call.  Returns True if successful."""
        ...

    def dial(self, sequence: str) -> None:
        """Dial a DTMF *sequence*."""
        ...

    def is_idle(self) -> bool:
        """Return True if the phone is in the idle state."""
        ...

    def is_dialing(self) -> bool:
        """Return True if the phone is currently dialling."""
        ...

    def is_incall_dialing(self) -> bool:
        """Return True if the phone is dialling while connected to an existing call
        (e.g. entering a transfer target during hold).
        """
        ...

    def is_ringing(self) -> bool:
        """Return True if the phone is ringing."""
        ...

    def is_connected(self) -> bool:
        """Return True if the phone has an active call connection."""
        ...

    def is_incall_connected(self) -> bool:
        """Return True if the phone has an in-progress second leg connected during a
        transfer or consultation.
        """
        ...

    def is_onhold(self) -> bool:
        """Return True if the current primary call is in a hold
        (re-INVITE sendonly / inactive) state.
        """
        ...

    def is_playing_dialtone(self) -> bool:
        """Return True if the phone is currently playing a dial tone."""
        ...

    def is_incall_playing_dialtone(self) -> bool:
        """Return True if the phone is emitting a dial tone during an in-call consultation."""
        ...

    def is_call_ended(self) -> bool:
        """Return True if the last call has ended."""
        ...

    def is_code_ended(self) -> bool:
        """Return True if the last feature-code dial sequence has finished
        (no more DTMF digits will be sent).
        """
        ...

    def is_call_waiting(self) -> bool:
        """Return True if a second incoming call is currently waiting while the
        primary call is connected.
        """
        ...

    def is_in_conference(self) -> bool:
        """Return True if this phone is currently a participant in a three-way or
        larger conference bridge.
        """
        ...

    def has_off_hook_warning(self) -> bool:
        """Return True if the phone is playing an off-hook warning tone
        (handset left off-hook without dialling).
        """
        ...

    def detect_dialtone(self) -> bool:
        """Return True if a dial tone is detected on the line."""
        ...

    def is_line_busy(self) -> bool:
        """Return True if the line is busy."""
        ...

    def reply_with_code(self, code: int) -> None:
        """Reply to an incoming call or event with the given SIP response *code*."""
        ...

    def is_call_not_answered(self) -> bool:
        """Return True if the outgoing call was not answered."""
        ...

    def answer_waiting_call(self) -> None:
        """Answer the waiting call and place the primary call on hold."""
        ...

    def toggle_call(self) -> None:
        """Swap which call is active: place the currently-active call on hold and
        resume the held call.
        """
        ...

    def merge_two_calls(self) -> None:
        """Merge the active and held calls into a single conference bridge."""
        ...

    def reject_waiting_call(self) -> None:
        """Reject the waiting call with 486 Busy Here; the primary call remains connected."""
        ...

    def place_call_onhold(self) -> None:
        """Place the active call on hold."""
        ...

    def place_call_offhold(self) -> None:
        """Resume the held call."""
        ...

    def press_R_button(self) -> None:
        """Press the R (recall/flash) button on the phone."""
        ...

    def hook_flash(self) -> None:
        """Send a hook-flash signal."""
        ...

    def wait_for_state(self, state: str, timeout: int = 10) -> bool:
        """Wait up to *timeout* seconds for the phone to reach *state*.

        Returns True if the state was reached within the timeout.
        """
        ...

    def press_buttons(self, buttons: str) -> None:
        """Press the DTMF *buttons* sequence on the phone keypad."""
        ...

    # ------------------------------------------------------------------
    # MWI / voicemail indicators (v0.2.0+)
    # ------------------------------------------------------------------

    def has_mwi_indicator(self) -> bool:
        """Return True if the phone's MWI indicator (lamp/display) is active.

        A conformant driver observes the phone's SIP NOTIFY stream for
        ``message-summary`` events and exposes the current waiting flag here.
        """
        ...

    def check_voicemail(self) -> None:
        """Dial the voicemail-access feature code (e.g. ``*97``)."""
        ...

    # ------------------------------------------------------------------
    # Presence (v0.2.0+)
    # ------------------------------------------------------------------

    def is_away(self) -> bool:
        """Return True if the phone is currently in an away/unavailable presence state."""
        ...

    def set_presence(self, status: str) -> None:
        """Publish the local presence *status* for this phone.

        Typical values: ``"online"``, ``"busy"``, ``"away"``, ``"offline"``.
        Implementers emit a SIP PUBLISH with a ``presence`` event package.
        """
        ...

    # ------------------------------------------------------------------
    # Offline SIP MESSAGE (v0.2.0+)
    # ------------------------------------------------------------------

    def has_pending_offline_message(self) -> bool:
        """Return True if a stored-while-offline SIP MESSAGE is pending delivery.

        Expected to flip True after a REGISTER that flushes msilo-stored
        messages, and back to False once the UA has acknowledged them.
        """
        ...
