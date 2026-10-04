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
dicts. Each has ``as_dict()``, the released dict, for the deprecated readers to return.
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


class PresenceStatus(StrEnum):
    """A presence status. Open: a provider may report other words (``OTHER``)."""

    ONLINE = "online"
    BUSY = "busy"
    AWAY = "away"
    OFFLINE = "offline"
    OTHER = "other"


class SipMethod(StrEnum):
    """A SIP request method. Open: an extension method or a log marker is ``OTHER``.

    The RFC 3261 methods plus the extension methods the contract's docstrings name
    (``MESSAGE``, ``NOTIFY``, ``PUBLISH``).
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


def _count(owner: str, name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{owner}.{name} takes an int, not {value!r}")
    if value < 0:
        raise ValueError(f"{owner}.{name} cannot be negative: {value}")


def _flag(owner: str, name: str, value: object) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{owner}.{name} takes a bool, not {value!r}")


def _text(owner: str, name: str, value: object) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{owner}.{name} takes text, not {value!r}")


def _when(owner: str, name: str, value: object) -> None:
    if not isinstance(value, datetime):
        raise TypeError(f"{owner}.{name} takes a datetime, not {value!r}")


@dataclass(frozen=True)
class RtpStats:
    """What a SIP server's media relay reports: whether it is engaged on any call and
    how many sessions it holds."""

    engaged: bool
    sessions: int

    def __post_init__(self) -> None:
        _flag("RtpStats", "engaged", self.engaged)
        _count("RtpStats", "sessions", self.sessions)

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
        _flag("MwiStatus", "waiting", self.waiting)
        _count("MwiStatus", "new", self.new)
        _count("MwiStatus", "old", self.old)

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
        _text("OfflineMessage", "sender", self.sender)
        _text("OfflineMessage", "body", self.body)
        _when("OfflineMessage", "stored_at", self.stored_at)

    def as_dict(self) -> dict[str, object]:
        """The released ``get_offline_messages`` entry: ``from``, ``body`` and
        ``timestamp`` (ISO-8601 text)."""
        return {"from": self.sender, "body": self.body, "timestamp": self.stored_at.isoformat()}
