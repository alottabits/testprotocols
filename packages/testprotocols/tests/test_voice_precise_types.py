"""Voice vocabularies and records."""

from __future__ import annotations

import dataclasses
import inspect
from datetime import datetime

import pytest
from testprotocols.deprecation import coerce_enum
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
        coerce_enum(PhoneState, "spinning", what="wait_for_state(state)")


def test_presence_parameters_and_returns_are_str() -> None:
    for fn in (SipPhone.set_presence, SipServer.notify_presence):
        assert inspect.signature(fn).parameters["status"].annotation == "str"
    assert inspect.signature(SipServer.get_user_presence).return_annotation == "str"


def test_verify_sip_message_signature() -> None:
    params = inspect.signature(SipServer.verify_sip_message).parameters
    assert params["message_type"].annotation == "str"
    assert params["since"].annotation == "datetime | None"
    assert params["since"].default is None


def test_new_members_exist() -> None:
    for name in ("read_rtpengine_stats", "read_mwi_status", "read_offline_messages"):
        assert callable(getattr(SipServer, name))
    # the deprecated names stay
    for name in ("get_rtpengine_stats", "get_mwi_status", "get_offline_messages"):
        assert callable(getattr(SipServer, name))


def test_rtp_stats_as_dict_is_the_released_dict() -> None:
    # the example implementer returned {"engaged": bool, "sessions": int}
    assert RtpStats(engaged=True, sessions=2).as_dict() == {"engaged": True, "sessions": 2}


def test_mwi_status_as_dict_is_the_released_dict() -> None:
    assert MwiStatus(waiting=True, new=2, old=1).as_dict() == {
        "waiting": True,
        "new": 2,
        "old": 1,
    }


def test_offline_message_as_dict_is_the_released_entry() -> None:
    # the implementer's own text: the database's "date time" form
    when = datetime.fromisoformat("2026-04-22 10:00:00")
    msg = OfflineMessage(sender="sip:a@x", body="hi", stored_at=when)
    assert msg.as_dict() == {"from": "sip:a@x", "body": "hi", "timestamp": "2026-04-22 10:00:00"}


def test_offline_message_round_trips_the_implementer_text() -> None:
    row = ("sip:a@x", "hi", "2026-04-22 10:00:00")
    msg = OfflineMessage(row[0], row[1], datetime.fromisoformat(row[2]))
    assert msg.as_dict() == {"from": row[0], "body": row[1], "timestamp": row[2]}


def test_offline_message_aware_datetime_keeps_its_offset() -> None:
    when = datetime.fromisoformat("2026-04-22 10:00:00+02:00")
    msg = OfflineMessage(sender="s", body="b", stored_at=when)
    assert msg.as_dict()["timestamp"] == "2026-04-22 10:00:00+02:00"
    assert (
        OfflineMessage("s", "b", datetime.fromisoformat("2026-04-22 10:00:00")).as_dict()[
            "timestamp"
        ]
        == "2026-04-22 10:00:00"
    )


@pytest.mark.parametrize(
    "build",
    [
        lambda: RtpStats(engaged=1, sessions=0),  # type: ignore[arg-type]
        lambda: RtpStats(engaged=True, sessions=True),
        lambda: MwiStatus(waiting="yes", new=0, old=0),  # type: ignore[arg-type]
        lambda: MwiStatus(waiting=True, new="1", old=0),  # type: ignore[arg-type]
        lambda: OfflineMessage(sender="a", body="b", stored_at="2026-10-04"),  # type: ignore[arg-type]
        lambda: OfflineMessage(sender=1, body="b", stored_at=datetime(2026, 1, 1)),  # type: ignore[arg-type]
    ],
)
def test_records_refuse_wrong_types(build) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(TypeError):
        build()


def test_records_refuse_negative_counts() -> None:
    with pytest.raises(ValueError, match="negative"):
        MwiStatus(waiting=False, new=-1, old=0)
    with pytest.raises(ValueError, match="negative"):
        RtpStats(engaged=False, sessions=-1)


def test_records_are_frozen() -> None:
    stats = RtpStats(engaged=True, sessions=1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        stats.sessions = 2  # type: ignore[misc]
