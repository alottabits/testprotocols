"""Typing-only conformance: the ``_renamed`` accessor Protocols match the host-tier contracts.

The accessors cast a driver's member to a precise callable Protocol, so a drift between that
Protocol and the contract would otherwise go unseen. Each assignment below is checked by mypy
and pyright: a changed member that no longer fits its accessor shape fails the type check,
not a test.
"""

from __future__ import annotations

from testoperations._renamed import (
    InjectEvent,
    InjectTransient,
    StartReceiverSession,
    StartSenderSession,
    StartTrafficReceiver,
    StartTrafficSender,
)
from testprotocols.iperf_client import IperfClient
from testprotocols.iperf_server import IperfServer
from testprotocols.netem_controller import NetemController


def _accessor_shapes_match_the_contract(
    client: IperfClient, server: IperfServer, netem: NetemController
) -> None:
    _start_sender_session: StartSenderSession = client.start_sender_session
    _start_traffic_sender: StartTrafficSender = client.start_traffic_sender  # type: ignore[deprecated]  # the released member under test
    _start_receiver_session: StartReceiverSession = server.start_receiver_session
    _start_traffic_receiver: StartTrafficReceiver = server.start_traffic_receiver  # type: ignore[deprecated]  # the released member under test
    _inject_event: InjectEvent = netem.inject_event
    _inject_transient: InjectTransient = netem.inject_transient  # type: ignore[deprecated]  # the released member under test


def test_accessor_shapes_are_checked_by_the_type_checkers() -> None:
    # Nothing to run: the assignments above are the check.
    assert callable(_accessor_shapes_match_the_contract)
