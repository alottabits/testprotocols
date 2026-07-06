"""Tests for testoperations.throughput (concurrent iperf3 measurement framing)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from testoperations.throughput import (
    ThroughputFlow,
    count_sessions,
    iter_json_docs,
    last_session_mbps,
    last_session_rtt_ms,
    measure_concurrent_throughput,
)


def _session_doc(
    rx_bps: float | None = None,
    sum_bps: float | None = None,
    rtt_us: list[tuple[float, float]] | None = None,
) -> str:
    """One iperf3 session JSON; *rtt_us* adds streams with (min_rtt, mean_rtt) µs."""
    end: dict[str, object] = {}
    if rx_bps is not None:
        end["sum_received"] = {"bits_per_second": rx_bps}
    if sum_bps is not None:
        end["sum"] = {"bits_per_second": sum_bps}
    if rtt_us is not None:
        end["streams"] = [{"sender": {"min_rtt": mn, "mean_rtt": mean}} for mn, mean in rtt_us]
    return json.dumps({"start": {"test_start": {}}, "end": end}, indent=2)


# --- JSON log parsing ---------------------------------------------------------


class TestLogParsing:
    def test_iter_json_docs_multiple_documents(self) -> None:
        text = _session_doc(rx_bps=1e6) + "\n" + _session_doc(rx_bps=2e6)
        assert len(iter_json_docs(text)) == 2

    def test_iter_json_docs_ignores_trailing_incomplete_document(self) -> None:
        text = _session_doc(rx_bps=1e6) + '\n{"start": {"test_start"'
        assert len(iter_json_docs(text)) == 1

    def test_iter_json_docs_braces_inside_strings_do_not_confuse_scanner(self) -> None:
        text = json.dumps({"note": "brace } in { string", "end": {}})
        docs = iter_json_docs(text)
        assert len(docs) == 1
        assert docs[0]["note"] == "brace } in { string"

    def test_count_sessions_empty_log(self) -> None:
        assert count_sessions("") == 0

    def test_last_session_mbps_prefers_receive_side_of_last_doc(self) -> None:
        text = _session_doc(rx_bps=100e6) + "\n" + _session_doc(rx_bps=47.5e6)
        assert last_session_mbps(text) == pytest.approx(47.5)

    def test_last_session_mbps_falls_back_to_sum(self) -> None:
        assert last_session_mbps(_session_doc(sum_bps=9e6)) == pytest.approx(9.0)

    def test_last_session_mbps_none_when_no_summary(self) -> None:
        assert last_session_mbps("") is None
        assert last_session_mbps(json.dumps({"end": {}})) is None

    def test_last_session_rtt_converts_microseconds_to_ms(self) -> None:
        text = _session_doc(rx_bps=1e6, rtt_us=[(480.0, 1250.0)])
        min_ms, mean_ms = last_session_rtt_ms(text)
        assert min_ms == pytest.approx(0.48)
        assert mean_ms == pytest.approx(1.25)

    def test_last_session_rtt_aggregates_streams_min_of_min_mean_of_mean(self) -> None:
        text = _session_doc(rx_bps=1e6, rtt_us=[(400.0, 1000.0), (600.0, 3000.0)])
        min_ms, mean_ms = last_session_rtt_ms(text)
        assert min_ms == pytest.approx(0.4)
        assert mean_ms == pytest.approx(2.0)

    def test_last_session_rtt_reads_the_last_document(self) -> None:
        text = (
            _session_doc(rx_bps=1e6, rtt_us=[(9000.0, 9000.0)])
            + "\n"
            + _session_doc(rx_bps=1e6, rtt_us=[(500.0, 700.0)])
        )
        min_ms, mean_ms = last_session_rtt_ms(text)
        assert min_ms == pytest.approx(0.5)
        assert mean_ms == pytest.approx(0.7)

    def test_last_session_rtt_none_when_absent(self) -> None:
        assert last_session_rtt_ms("") == (None, None)
        assert last_session_rtt_ms(_session_doc(rx_bps=1e6)) == (None, None)
        no_samples = json.dumps({"end": {"streams": [{"sender": {}}]}})
        assert last_session_rtt_ms(no_samples) == (None, None)

    def test_last_session_rtt_is_both_or_neither(self) -> None:
        # A half-populated sender block (only one of min/mean) must collapse
        # to (None, None) — callers rely on the pair being atomic.
        only_min = json.dumps({"end": {"streams": [{"sender": {"min_rtt": 500.0}}]}})
        assert last_session_rtt_ms(only_min) == (None, None)
        only_mean = json.dumps({"end": {"streams": [{"sender": {"mean_rtt": 900.0}}]}})
        assert last_session_rtt_ms(only_mean) == (None, None)


# --- measure_concurrent_throughput ---------------------------------------------


def _flow(
    port: int, mbps: float, *, stale_docs: int = 0
) -> tuple[ThroughputFlow, MagicMock, MagicMock]:
    """A flow over mocked capabilities; returns (flow, sender_mock, receiver_mock).

    The fake ``get_iperf_logs`` returns only the *stale* documents until the
    sender has been started, then appends the fresh session — mirroring the
    real sequencing (session completes only after the measurement window).
    """
    stale = "\n".join(_session_doc(rx_bps=1e6) for _ in range(stale_docs))
    fresh = stale + "\n" + _session_doc(rx_bps=mbps * 1e6)

    sender = MagicMock()
    sender.start_traffic_sender.return_value = (4000 + port, f"/tmp/cl_{port}.log")

    receiver = MagicMock()
    receiver.start_traffic_receiver.return_value = (5000 + port, f"/tmp/rx_{port}.log")
    receiver.get_iperf_logs.side_effect = lambda _log: (
        fresh if sender.start_traffic_sender.called else stale
    )
    # The sender's own --json log (forward-flow RTT source): a completed
    # session without RTT samples, so RTT resolution terminates immediately.
    sender.get_iperf_logs.side_effect = lambda _log: (
        _session_doc(rx_bps=mbps * 1e6) if sender.start_traffic_sender.called else ""
    )
    flow = ThroughputFlow(sender=sender, receiver=receiver, dest_host="192.168.32.3", port=port)
    return flow, sender, receiver


class TestMeasureConcurrentThroughput:
    def test_single_flow_returns_receive_rate(self) -> None:
        flow, _, _ = _flow(5301, mbps=47.5)
        results = measure_concurrent_throughput([flow], duration_s=10, sleep=lambda _s: None)
        assert [r.port for r in results] == [5301]
        assert results[0].mbps == pytest.approx(47.5)

    def test_receiver_started_before_sender_with_expected_args(self) -> None:
        flow, sender, receiver = _flow(5301, mbps=10.0)
        order: list[str] = []

        def _rx(port: int) -> tuple[int, str]:
            order.append(f"rx:{port}")
            return (5301, "/tmp/rx.log")

        def _tx(host: str, port: int, time: int, direction: str | None = None) -> tuple[int, str]:
            order.append(f"tx:{host}:{port}:t={time}:d={direction}")
            return (4001, "/tmp/tx.log")

        receiver.start_traffic_receiver.side_effect = _rx
        sender.start_traffic_sender.side_effect = _tx
        measure_concurrent_throughput([flow], duration_s=7, sleep=lambda _s: None)
        assert order == ["rx:5301", "tx:192.168.32.3:5301:t=7:d=--json"]

    def test_stale_sessions_in_log_are_not_read_as_results(self) -> None:
        # Two stale docs at 1 Mbps sit in the per-port log from an earlier run;
        # the fresh session measures 42 Mbps and must be the one reported.
        flow, _, _ = _flow(5301, mbps=42.0, stale_docs=2)
        results = measure_concurrent_throughput([flow], duration_s=10, sleep=lambda _s: None)
        assert results[0].mbps == pytest.approx(42.0)

    def test_concurrent_flows_all_senders_started_before_wait_and_ordered_results(self) -> None:
        flow_a, sender_a, _ = _flow(5301, mbps=9.5)
        flow_b, sender_b, _ = _flow(5302, mbps=11.0)
        sleeps: list[float] = []
        results = measure_concurrent_throughput(
            [flow_a, flow_b], duration_s=10, sleep=sleeps.append
        )
        assert [r.port for r in results] == [5301, 5302]
        assert [r.mbps for r in results] == [pytest.approx(9.5), pytest.approx(11.0)]
        # Both senders launched; the measurement wait happened exactly once.
        sender_a.start_traffic_sender.assert_called_once()
        sender_b.start_traffic_sender.assert_called_once()
        assert sleeps.count(10.0) == 1

    def test_duplicate_ports_rejected(self) -> None:
        flow_a, _, _ = _flow(5301, mbps=1.0)
        flow_b, _, _ = _flow(5301, mbps=2.0)
        with pytest.raises(ValueError, match="unique"):
            measure_concurrent_throughput([flow_a, flow_b], sleep=lambda _s: None)

    def test_timeout_when_no_new_session_appears(self) -> None:
        flow, _, receiver = _flow(5301, mbps=42.0)
        receiver.get_iperf_logs.side_effect = lambda _log: ""  # never completes
        clock = iter(float(t) for t in range(0, 1000, 5))
        with pytest.raises(RuntimeError, match="port 5301"):
            measure_concurrent_throughput(
                [flow],
                duration_s=10,
                result_timeout_s=20.0,
                sleep=lambda _s: None,
                monotonic=lambda: next(clock),
            )

    def test_both_sides_stopped_on_success(self) -> None:
        flow, sender, receiver = _flow(5301, mbps=5.0)
        measure_concurrent_throughput([flow], duration_s=10, sleep=lambda _s: None)
        sender.stop_traffic.assert_called_once_with(4000 + 5301)
        receiver.stop_traffic.assert_called_once_with(5000 + 5301)

    def test_cleanup_runs_even_when_measurement_times_out(self) -> None:
        flow, sender, receiver = _flow(5301, mbps=5.0)
        receiver.get_iperf_logs.side_effect = lambda _log: ""
        clock = iter(float(t) for t in range(0, 1000, 5))
        with pytest.raises(RuntimeError):
            measure_concurrent_throughput(
                [flow],
                duration_s=10,
                result_timeout_s=15.0,
                sleep=lambda _s: None,
                monotonic=lambda: next(clock),
            )
        sender.stop_traffic.assert_called_once()
        receiver.stop_traffic.assert_called_once()

    def test_cleanup_swallows_stop_errors(self) -> None:
        flow, sender, receiver = _flow(5301, mbps=5.0)
        sender.stop_traffic.side_effect = RuntimeError("already gone")
        receiver.stop_traffic.side_effect = RuntimeError("already gone")
        results = measure_concurrent_throughput([flow], duration_s=10, sleep=lambda _s: None)
        assert results[0].mbps == pytest.approx(5.0)


class TestDirectionAndRtt:
    def test_default_flow_sends_json_only(self) -> None:
        # --json is unconditional: the sender's own log is the forward-flow
        # RTT source, so it must always be machine-readable.
        flow, sender, _ = _flow(5301, mbps=5.0)
        measure_concurrent_throughput([flow], duration_s=10, sleep=lambda _s: None)
        kwargs = sender.start_traffic_sender.call_args.kwargs
        assert kwargs["direction"] == "--json"

    def test_reverse_flow_sends_dash_r(self) -> None:
        base, sender, _ = _flow(5301, mbps=5.0)
        flow = ThroughputFlow(
            sender=base.sender,
            receiver=base.receiver,
            dest_host=base.dest_host,
            port=base.port,
            reverse=True,
        )
        measure_concurrent_throughput([flow], duration_s=10, sleep=lambda _s: None)
        assert sender.start_traffic_sender.call_args.kwargs["direction"] == "-R --json"

    def test_omit_composes_with_reverse_and_extends_the_wait(self) -> None:
        base, sender, _ = _flow(5301, mbps=5.0)
        flow = ThroughputFlow(
            sender=base.sender,
            receiver=base.receiver,
            dest_host=base.dest_host,
            port=base.port,
            reverse=True,
            omit_s=3,
        )
        sleeps: list[float] = []
        measure_concurrent_throughput([flow], duration_s=10, sleep=sleeps.append)
        assert sender.start_traffic_sender.call_args.kwargs["direction"] == "-R -O 3 --json"
        assert sleeps.count(13.0) == 1

    def test_forward_flow_rtt_comes_from_the_senders_own_log(self) -> None:
        # Live-diagnosed 2026-07-06: the server-side log carries NO sender RTT
        # for client-sent sessions — the client's own --json log is the source.
        # The receiver doc deliberately carries a DIFFERENT (decoy) RTT.
        flow, sender, receiver = _flow(5301, mbps=42.0)
        receiver.get_iperf_logs.side_effect = lambda _log: (
            _session_doc(rx_bps=42e6, rtt_us=[(9999.0, 9999.0)])
            if sender.start_traffic_sender.called
            else ""
        )
        sender.get_iperf_logs.side_effect = lambda _log: (
            _session_doc(rx_bps=42e6, rtt_us=[(480.0, 1250.0)])
            if sender.start_traffic_sender.called
            else ""
        )
        (result,) = measure_concurrent_throughput([flow], duration_s=10, sleep=lambda _s: None)
        assert result.mbps == pytest.approx(42.0)
        assert result.min_rtt_ms == pytest.approx(0.48)
        assert result.mean_rtt_ms == pytest.approx(1.25)

    def test_reverse_flow_reads_rate_from_client_and_rtt_from_receiver(self) -> None:
        # Live-diagnosed 2026-07-06: in reverse mode the listening server
        # TRANSMITS — its log's sum_received is ~0 (a decoy here) while the
        # real received goodput is in the initiating client's own log; the
        # server's log is where the sending socket's TCP_INFO lives.
        base, sender, receiver = _flow(5301, mbps=42.0)
        flow = ThroughputFlow(
            sender=base.sender,
            receiver=base.receiver,
            dest_host=base.dest_host,
            port=base.port,
            reverse=True,
        )
        receiver.get_iperf_logs.side_effect = lambda _log: (
            _session_doc(rx_bps=0.0, rtt_us=[(480.0, 1250.0)])
            if sender.start_traffic_sender.called
            else ""
        )
        sender.get_iperf_logs.side_effect = lambda _log: (
            _session_doc(rx_bps=42e6) if sender.start_traffic_sender.called else ""
        )
        (result,) = measure_concurrent_throughput([flow], duration_s=10, sleep=lambda _s: None)
        assert result.mbps == pytest.approx(42.0)
        assert result.min_rtt_ms == pytest.approx(0.48)
        assert result.mean_rtt_ms == pytest.approx(1.25)

    def test_reverse_flow_without_client_session_raises(self) -> None:
        # The reverse rate lives in the client's log; if that never completes
        # there is no result to report — an operational failure, not a 0.0.
        base, sender, _ = _flow(5301, mbps=42.0)
        flow = ThroughputFlow(
            sender=base.sender,
            receiver=base.receiver,
            dest_host=base.dest_host,
            port=base.port,
            reverse=True,
        )
        sender.get_iperf_logs.side_effect = lambda _log: ""  # no session, ever
        clock = iter(float(t) for t in range(0, 1000, 5))
        with pytest.raises(RuntimeError, match="reverse flow on port 5301"):
            measure_concurrent_throughput(
                [flow],
                duration_s=10,
                result_timeout_s=20.0,
                sleep=lambda _s: None,
                monotonic=lambda: next(clock),
            )

    def test_results_rtt_none_when_session_has_no_samples(self) -> None:
        flow, _, _ = _flow(5301, mbps=5.0)
        (result,) = measure_concurrent_throughput([flow], duration_s=10, sleep=lambda _s: None)
        assert result.min_rtt_ms is None
        assert result.mean_rtt_ms is None

    def test_sender_log_never_completing_degrades_rtt_not_the_rate(self) -> None:
        flow, sender, _ = _flow(5301, mbps=42.0)
        sender.get_iperf_logs.side_effect = lambda _log: ""  # no session, ever
        clock = iter(float(t) for t in range(0, 1000, 5))
        (result,) = measure_concurrent_throughput(
            [flow],
            duration_s=10,
            result_timeout_s=20.0,
            sleep=lambda _s: None,
            monotonic=lambda: next(clock),
        )
        assert result.mbps == pytest.approx(42.0)
        assert result.min_rtt_ms is None
        assert result.mean_rtt_ms is None
