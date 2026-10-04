"""Typing-only conformance: the ``_renamed`` accessor Protocols match the host-tier contracts.

The accessors cast a driver's member to a precise callable Protocol, so a drift between that
Protocol and the contract would otherwise go unseen. Each assignment below is checked by mypy
and pyright: a changed member that no longer fits its accessor shape fails the type check,
not a test.
"""

from __future__ import annotations

from testoperations._renamed import (
    GetParameterValues,
    Gpv,
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
from testprotocols.tr069_server import Tr069Server


def _tr069_accessor_shapes_match_the_contract(acs: Tr069Server) -> None:
    get_parameter_values: GetParameterValues = acs.get_parameter_values
    gpv: Gpv = acs.GPV
    del get_parameter_values, gpv


def _accessor_shapes_match_the_contract(
    client: IperfClient, server: IperfServer, netem: NetemController
) -> None:
    start_sender_session: StartSenderSession = client.start_sender_session
    start_traffic_sender: StartTrafficSender = client.start_traffic_sender
    start_receiver_session: StartReceiverSession = server.start_receiver_session
    start_traffic_receiver: StartTrafficReceiver = server.start_traffic_receiver
    inject_event: InjectEvent = netem.inject_event
    inject_transient: InjectTransient = netem.inject_transient
    del start_sender_session, start_traffic_sender, start_receiver_session
    del start_traffic_receiver, inject_event, inject_transient


def test_accessor_shapes_are_checked_by_the_type_checkers() -> None:
    # Nothing to run: the assignments above are the check.
    assert callable(_accessor_shapes_match_the_contract)
    assert callable(_tr069_accessor_shapes_match_the_contract)
