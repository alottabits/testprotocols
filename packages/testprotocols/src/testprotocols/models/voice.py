"""Voice vocabularies and records: SIP phone states and the SIP server's observation
records.

``PhoneState`` is a ``StrEnum`` whose members equal the strings the released contract and
its implementers used. Presence statuses and SIP methods are the provider's own words and
travel as ``str``.

``RtpStats``, ``MwiStatus`` and ``OfflineMessage`` are the typed forms of what
``get_rtpengine_stats``, ``get_mwi_status`` and ``get_offline_messages`` returned as
dicts. Each has ``as_dict()``, the released dict shape, for the deprecated readers to return
(for ``OfflineMessage`` the timestamp text has one fixed format, see its ``as_dict``).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from testprotocols.models import _checks


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
    how many sessions it holds."""

    engaged: bool
    sessions: int

    def __post_init__(self) -> None:
        _checks.flag("RtpStats", "engaged", self.engaged)
        _checks.count("RtpStats", "sessions", self.sessions)

    def as_dict(self) -> dict[str, object]:
        """The released ``get_rtpengine_stats`` dict (``engaged``, ``sessions``)."""
        return {"engaged": self.engaged, "sessions": self.sessions}


@dataclass(frozen=True)
class MwiStatus:
    """A user's message-waiting indication: the waiting flag and the counts of new
    (unheard) and old (heard but retained) messages."""

    waiting: bool
    new: int
    old: int

    def __post_init__(self) -> None:
        _checks.flag("MwiStatus", "waiting", self.waiting)
        _checks.count("MwiStatus", "new", self.new)
        _checks.count("MwiStatus", "old", self.old)

    def as_dict(self) -> dict[str, object]:
        """The released ``get_mwi_status`` dict (``waiting``, ``new``, ``old``)."""
        return {"waiting": self.waiting, "new": self.new, "old": self.old}


@dataclass(frozen=True)
class OfflineMessage:
    """A SIP MESSAGE stored while its addressee was offline: the sender URI, the body
    and when it was stored."""

    sender: str
    body: str
    stored_at: datetime

    def __post_init__(self) -> None:
        _checks.text("OfflineMessage", "sender", self.sender)
        _checks.text("OfflineMessage", "body", self.body)
        _checks.when("OfflineMessage", "stored_at", self.stored_at)

    def as_dict(self) -> dict[str, object]:
        """The released ``get_offline_messages`` entry shape: ``from``, ``body`` and
        ``timestamp``: ``stored_at.isoformat(sep=" ")``, ISO-8601 with a space between
        date and time (``"2026-04-22 10:00:00"``). A naive datetime stays naive and an
        aware one keeps its offset. This is the text the one released implementer
        returns; a driver whose own text differs may keep returning that text from its
        deprecated reader instead of calling this."""
        return {
            "from": self.sender,
            "body": self.body,
            "timestamp": self.stored_at.isoformat(sep=" "),
        }
