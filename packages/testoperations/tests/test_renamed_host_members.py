"""Operations move to the host-tier members' new names, with an old-name fallback.

Each operation is run against a driver that has only the released (old) member and one that
has the new member: the old-name driver receives exactly the released call, the new-name
driver the typed call, and it never reaches its deprecated alias.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from unittest.mock import MagicMock

import pytest
from testoperations import netem_controller as netem_ops
from testoperations._renamed import (
    inject_event_of,
    inject_transient_of,
    start_receiver_session,
    start_sender_session,
)
from testoperations.sdwan import measure_failover_convergence
from testoperations.throughput import (
    ExternalFlow,
    ThroughputFlow,
    measure_concurrent_throughput,
    measure_external_flow,
)
from testprotocols.models import (
    Blackout,
    Brownout,
    IperfProcess,
    LatencySpike,
    PacketStorm,
)

NETEM_OLD = ["inject_transient", "set_impairment_profile", "set_interface_profile", "clear"]
NETEM_NEW = [*NETEM_OLD, "inject_event"]


def _old_netem() -> MagicMock:
    return MagicMock(spec=NETEM_OLD)


def _new_netem() -> MagicMock:
    return MagicMock(spec=NETEM_NEW)


# --- netem: transient events ----------------------------------------------------------


def _blackout(n: MagicMock) -> None:
    netem_ops.inject_blackout(n, duration_ms=2000)


def _brownout(n: MagicMock) -> None:
    netem_ops.inject_brownout(n, duration_ms=3000, loss_percent=50.0)


def _spike(n: MagicMock) -> None:
    netem_ops.inject_latency_spike(n, duration_ms=1000, latency_ms=500)


def _storm(n: MagicMock) -> None:
    netem_ops.inject_packet_storm(n, duration_ms=500, duplicate_percent=100.0)


@pytest.mark.parametrize(
    ("call", "released", "typed"),
    [
        (
            _blackout,
            (("blackout", 2000), dict[str, object]()),
            (Blackout(), 2000),
        ),
        (
            _brownout,
            (("brownout", 3000), {"loss_percent": 50.0}),
            (Brownout(loss_percent=50.0), 3000),
        ),
        (
            _spike,
            (("latency_spike", 1000), {"latency_ms": 500}),
            (LatencySpike(latency_ms=500), 1000),
        ),
        (
            _storm,
            (("packet_storm", 500), {"duplicate_percent": 100.0}),
            (PacketStorm(duplicate_percent=100.0), 500),
        ),
    ],
)
def test_netem_operation_works_with_old_and_new_name_drivers(
    call: Callable[[MagicMock], None],
    released: tuple[tuple[object, ...], dict[str, object]],
    typed: tuple[object, ...],
) -> None:
    old = _old_netem()
    call(old)
    old.inject_transient.assert_called_once_with(*released[0], **released[1])

    new = _new_netem()
    call(new)
    new.inject_event.assert_called_once_with(*typed)
    new.inject_transient.assert_not_called()


def test_packet_storm_loss_percent_reaches_both_driver_kinds() -> None:
    old = _old_netem()
    netem_ops.inject_packet_storm(old, duration_ms=500, loss_percent=20.0)
    old.inject_transient.assert_called_once_with(
        "packet_storm", 500, duplicate_percent=100.0, loss_percent=20.0
    )
    new = _new_netem()
    netem_ops.inject_packet_storm(new, duration_ms=500, loss_percent=20.0)
    new.inject_event.assert_called_once_with(
        PacketStorm(loss_percent=20.0, duplicate_percent=100.0), 500
    )


def test_failover_convergence_works_with_old_and_new_name_drivers() -> None:
    def old_check(n: MagicMock) -> None:
        n.inject_transient.assert_called_once_with("blackout", 3000)

    def new_check(n: MagicMock) -> None:
        n.inject_event.assert_called_once_with(Blackout(), 3000)

    for netem, check in ((_old_netem(), old_check), (_new_netem(), new_check)):
        router = MagicMock()
        router.get_active_wan_interface.side_effect = ["wan0", "wan1"]
        assert measure_failover_convergence(netem, router, "wan0", timeout_ms=3000) >= 0
        check(netem)


def test_accessor_prefers_the_new_name() -> None:
    new = _new_netem()
    assert inject_event_of(new) is new.inject_event
    assert inject_event_of(_old_netem()) is None
    old = _old_netem()
    assert inject_transient_of(old) is old.inject_transient


def test_accessor_refuses_a_non_callable_member() -> None:
    driver = MagicMock(spec=["inject_event"])
    driver.inject_event = 5
    with pytest.raises(TypeError, match="inject_event"):
        inject_event_of(driver)


# --- iperf: sessions ------------------------------------------------------------------

SENDER_OLD = ["start_traffic_sender", "stop_traffic", "get_iperf_logs"]
SENDER_NEW = [*SENDER_OLD, "start_sender_session"]
RECEIVER_OLD = ["start_traffic_receiver", "stop_traffic", "get_iperf_logs"]
RECEIVER_NEW = [*RECEIVER_OLD, "start_receiver_session"]


def _doc(mbps: float) -> str:
    bps = mbps * 1e6
    return json.dumps(
        {
            "start": {"test_start": {}},
            "end": {
                "sum_sent": {"bits_per_second": bps, "retransmits": 0},
                "sum_received": {"bits_per_second": bps},
            },
        }
    )


def _log_once(started: MagicMock) -> Callable[[str], str]:
    """A ``get_iperf_logs`` that yields a completed session once the sender has started."""

    def read(_log: str) -> str:
        return _doc(40.0) if started.called else ""

    return read


def _sender(new: bool) -> MagicMock:
    sender = MagicMock(spec=SENDER_NEW if new else SENDER_OLD)
    if new:
        sender.start_sender_session.return_value = IperfProcess(4100, "/tmp/cl.log")
    else:
        sender.start_traffic_sender.return_value = (4100, "/tmp/cl.log")
    started = sender.start_sender_session if new else sender.start_traffic_sender
    sender.get_iperf_logs.side_effect = _log_once(started)
    return sender


def _receiver(new: bool, sender: MagicMock) -> MagicMock:
    receiver = MagicMock(spec=RECEIVER_NEW if new else RECEIVER_OLD)
    if new:
        receiver.start_receiver_session.return_value = IperfProcess(5100, "/tmp/rx.log")
    else:
        receiver.start_traffic_receiver.return_value = (5100, "/tmp/rx.log")
    started = (
        sender.start_sender_session
        if hasattr(sender, "start_sender_session")
        else (sender.start_traffic_sender)
    )
    receiver.get_iperf_logs.side_effect = _log_once(started)
    return receiver


@pytest.mark.parametrize("new", [False, True])
def test_concurrent_throughput_works_with_old_and_new_name_drivers(new: bool) -> None:
    sender = _sender(new)
    receiver = _receiver(new, sender)
    flow = ThroughputFlow(
        sender=sender, receiver=receiver, dest_host="192.0.2.3", port=5301, window="8M"
    )
    results = measure_concurrent_throughput([flow], duration_s=1, sleep=lambda _s: None)
    assert results[0].mbps == pytest.approx(40.0)  # pyright: ignore[reportUnknownMemberType]
    if new:
        receiver.start_receiver_session.assert_called_once_with(5301)
        kwargs = sender.start_sender_session.call_args.kwargs
        assert kwargs["window_bytes"] == 8 * 1024 * 1024 and "window" not in kwargs
        sender.start_traffic_sender.assert_not_called()
        receiver.start_traffic_receiver.assert_not_called()
    else:
        receiver.start_traffic_receiver.assert_called_once_with(5301)
        assert sender.start_traffic_sender.call_args.kwargs["window"] == "8M"
    sender.stop_traffic.assert_called_once_with(4100)
    receiver.stop_traffic.assert_called_once_with(5100)


@pytest.mark.parametrize("new", [False, True])
def test_external_flow_works_with_old_and_new_name_drivers(new: bool) -> None:
    sender = _sender(new)
    result = measure_external_flow(
        ExternalFlow(sender=sender, dest_host="203.0.113.10", port=5201, window=None),
        duration_s=1,
        sleep=lambda _s: None,
    )
    assert result.mbps == pytest.approx(40.0)  # pyright: ignore[reportUnknownMemberType]
    start = sender.start_sender_session if new else sender.start_traffic_sender
    assert start.call_args.args == ("203.0.113.10", 5201)
    assert start.call_args.kwargs["json_output"] is True
    assert start.call_args.kwargs["window_bytes" if new else "window"] is None
    sender.stop_traffic.assert_called_once_with(4100)


def test_session_helpers_return_the_record_from_either_name() -> None:
    old = _sender(False)
    assert start_sender_session(old, "192.0.2.3", 5201, json_output=True) == IperfProcess(
        4100, "/tmp/cl.log"
    )
    rx_old = MagicMock(spec=RECEIVER_OLD)
    rx_old.start_traffic_receiver.return_value = (5100, "/tmp/rx.log")
    assert start_receiver_session(rx_old, 5201) == IperfProcess(5100, "/tmp/rx.log")


def test_sender_helper_refuses_a_malformed_window_for_a_new_name_driver() -> None:
    with pytest.raises(ValueError, match="window"):
        start_sender_session(_sender(True), "192.0.2.3", 5201, window="huge")
