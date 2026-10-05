"""Voice vocabularies and records: SIP phone states and the SIP server's observation
records.

``PhoneState`` is a ``StrEnum`` whose members equal the strings the released contract and
its implementers used. Presence statuses and SIP methods are the provider's own words and
travel as ``str``.

``RtpStats``, ``MwiStatus`` and ``OfflineMessage`` are the typed forms of what
``get_rtpengine_stats``, ``get_mwi_status`` and ``get_offline_messages`` returned as
dicts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PhoneState(StrEnum):
    """A state a SIP phone can be in, one per ``is_*`` predicate of ``SipPhone``.

    ``wait_for_state`` takes these words. The members ``IDLE``, ``DIALING``,
    ``RINGING``, ``CONNECTED``, ``DIALTONE``, ``CALL_ENDED``, ``BUSY``,
    ``NOT_ANSWERED`` and ``HOLD`` are the words the released implementer accepted
    (``HOLD`` is spelled ``"hold"``); the others mirror the remaining predicates.
    """

    IDLE = "idle"  # is_idle
    DIALING = "dialing"  # is_dialing
    INCALL_DIALING = "incall_dialing"  # is_incall_dialing
    RINGING = "ringing"  # is_ringing
    CONNECTED = "connected"  # is_connected
    INCALL_CONNECTED = "incall_connected"  # is_incall_connected
    HOLD = "hold"  # is_onhold
    DIALTONE = "dialtone"  # is_playing_dialtone
    INCALL_DIALTONE = "incall_dialtone"  # is_incall_playing_dialtone
    CALL_ENDED = "call_ended"  # is_call_ended
    CODE_ENDED = "code_ended"  # is_code_ended
    CALL_WAITING = "call_waiting"  # is_call_waiting
    CONFERENCE = "conference"  # is_in_conference
    BUSY = "busy"  # is_line_busy
    NOT_ANSWERED = "not_answered"  # is_call_not_answered


@dataclass(frozen=True)
class RtpStats:
    """What a SIP server's media relay reports: whether it is engaged on any call and
    how many sessions it holds (not negative)."""

    engaged: bool
    sessions: int


@dataclass(frozen=True)
class MwiStatus:
    """A user's message-waiting indication: the waiting flag and the counts of new
    (unheard) and old (heard but retained) messages, each not negative."""

    waiting: bool
    new: int
    old: int


@dataclass(frozen=True)
class OfflineMessage:
    """A SIP MESSAGE stored while its addressee was offline: the sender URI, the body
    and when it was stored."""

    sender: str
    body: str
    stored_at: datetime
