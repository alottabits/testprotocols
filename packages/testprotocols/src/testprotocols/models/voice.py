"""Voice vocabularies and records: SIP phone states, presence, SIP methods and the
SIP server's observation records.

``PhoneState``, ``PresenceStatus`` and ``SipMethod`` are ``StrEnum`` whose members
equal the strings the released contract and its implementers used. ``PresenceStatus``
and ``SipMethod`` are open: a provider may report a word they do not list, which
travels as ``OTHER`` with the raw word (shape 3o). A *parameter* typed
``PresenceStatus | str`` or ``SipMethod | str`` is resolved by a driver with
:func:`testprotocols.deprecation.coerce_open_enum`: a member passes, a plain string
naming a member converts and warns, and any other string is the raw word, passed on
unchanged with no error and no warning.

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


class PresenceStatus(StrEnum):
    """A presence status. Open: a provider may report other words (``OTHER``).

    Edge case of the shared helper: a raw device word equal to a member value
    (``"other"``) names that member and is not kept as a raw word.
    """

    ONLINE = "online"
    BUSY = "busy"
    AWAY = "away"
    OFFLINE = "offline"
    OTHER = "other"


class SipMethod(StrEnum):
    """A SIP request method. Open: an extension method or a log marker is ``OTHER``.

    The RFC 3261 methods plus the extension methods the contract's docstrings name
    (``MESSAGE``, ``NOTIFY``, ``PUBLISH``). A raw device word equal to a member value
    (``"OTHER"``) names that member and is not kept as a raw word (an edge case of the
    shared helper).
    """

    INVITE = "INVITE"
    ACK = "ACK"
    BYE = "BYE"
    CANCEL = "CANCEL"
    OPTIONS = "OPTIONS"
    REGISTER = "REGISTER"
    MESSAGE = "MESSAGE"
    NOTIFY = "NOTIFY"
    PUBLISH = "PUBLISH"
    OTHER = "OTHER"


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
