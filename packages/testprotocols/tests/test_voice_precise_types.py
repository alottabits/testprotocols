"""Voice vocabularies and records."""

from __future__ import annotations

import dataclasses
import inspect
import typing
from datetime import datetime

import pytest
from testprotocols.models import (
    MwiStatus,
    OfflineMessage,
    PhoneState,
    RtpStats,
)
from testprotocols.sip_phone import SipPhone
from testprotocols.sip_server import SipServer

# Released words: the wait_for_state map of the example implementer, and the is_* predicates.
RELEASED_STATES = {
    "idle": "IDLE",
    "dialing": "DIALING",
    "ringing": "RINGING",
    "connected": "CONNECTED",
    "dialtone": "DIALTONE",
    "call_ended": "CALL_ENDED",
    "busy": "BUSY",
    "not_answered": "NOT_ANSWERED",
    "hold": "HOLD",
}


@pytest.mark.parametrize(("word", "name"), RELEASED_STATES.items())
def test_phone_state_members_equal_released_words(word: str, name: str) -> None:
    assert PhoneState[name] == word
    assert PhoneState(word) is PhoneState[name]


def test_phone_state_has_a_member_per_state_predicate() -> None:
    predicates = {
        n
        for n in dir(SipPhone)
        if n.startswith("is_") and n not in {"is_away"}  # presence, not call state
    }
    assert len(PhoneState) == len(predicates)


def test_phone_state_unknown_word_raises() -> None:
    with pytest.raises(ValueError, match="spinning"):
        PhoneState("spinning")


def test_presence_parameters_and_returns_are_str() -> None:
    for fn in (SipPhone.set_presence, SipServer.notify_presence):
        assert inspect.signature(fn).parameters["status"].annotation == "str"
    assert inspect.signature(SipServer.get_user_presence).return_annotation == "str"


def test_verify_sip_message_signature() -> None:
    params = inspect.signature(SipServer.verify_sip_message).parameters
    assert params["message_type"].annotation == "str"
    # the released annotation is kept; its narrowing to ``datetime | None`` is announced
    assert params["since"].annotation == "Any"
    assert params["since"].default is None


def test_new_members_exist() -> None:
    for name in ("read_rtpengine_stats", "read_mwi_status", "read_offline_messages"):
        assert callable(getattr(SipServer, name))
    # the deprecated names stay
    for name in ("get_rtpengine_stats", "get_mwi_status", "get_offline_messages"):
        assert callable(getattr(SipServer, name))


def test_records_hold_the_released_values() -> None:
    # the example implementer returned {"engaged": bool, "sessions": int},
    # {"waiting", "new", "old"} and the database's "date time" text for a stored message
    stats = RtpStats(engaged=True, sessions=2)
    assert (stats.engaged, stats.sessions) == (True, 2)
    mwi = MwiStatus(waiting=True, new=2, old=1)
    assert (mwi.waiting, mwi.new, mwi.old) == (True, 2, 1)
    row = ("sip:a@x", "hi", "2026-04-22 10:00:00")
    msg = OfflineMessage(row[0], row[1], datetime.fromisoformat(row[2]))
    assert msg.stored_at is not None
    assert (msg.sender, msg.body, msg.stored_at.isoformat(sep=" ")) == row


def test_offline_message_time_may_be_unreported() -> None:
    hints = typing.get_type_hints(OfflineMessage)
    assert hints["stored_at"] == datetime | None
    assert dataclasses.fields(OfflineMessage)[2].default is dataclasses.MISSING
    assert OfflineMessage("sip:a@x", "hi", None).stored_at is None


def test_records_are_frozen() -> None:
    stats = RtpStats(engaged=True, sessions=1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        stats.sessions = 2  # type: ignore[misc]
