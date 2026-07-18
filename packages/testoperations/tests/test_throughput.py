"""Tests for testoperations.throughput (concurrent iperf3 measurement framing)."""

from __future__ import annotations

import json
from dataclasses import replace
from unittest.mock import MagicMock

import pytest
from testoperations.throughput import (
    DEFAULT_PROBE_RATE_MBPS,
    DirectionSpec,
    ExternalFlow,
    FlowThroughput,
    NonCompletion,
    PathMeasurement,
    ThroughputFlow,
    count_sessions,
    iter_json_docs,
    last_session_error,
    last_session_mbps,
    last_session_retransmits,
    last_session_rtt_ms,
    measure_concurrent_throughput,
    measure_external_flow,
    measure_external_path_until,
    measure_one_direction,
    measure_path_rtt,
    measure_path_until,
)


def _session_doc(
    rx_bps: float | None = None,
    sum_bps: float | None = None,
    rtt_us: list[tuple[float, float]] | None = None,
    retransmits: int | None = None,
) -> str:
    """One iperf3 session JSON; *rtt_us* adds streams with (min_rtt, mean_rtt) µs."""
    end: dict[str, object] = {}
    if rx_bps is not None:
        end["sum_received"] = {"bits_per_second": rx_bps}
    if sum_bps is not None:
        end["sum"] = {"bits_per_second": sum_bps}
    if rtt_us is not None:
        end["streams"] = [{"sender": {"min_rtt": mn, "mean_rtt": mean}} for mn, mean in rtt_us]
    if retransmits is not None:
        end["sum_sent"] = {"retransmits": retransmits}
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

    def test_last_session_retransmits_reads_the_senders_summary(self) -> None:
        text = (
            _session_doc(rx_bps=1e6, retransmits=0)
            + "\n"
            + _session_doc(rx_bps=1e6, retransmits=203)
        )
        assert last_session_retransmits(text) == 203

    def test_last_session_retransmits_none_when_absent(self) -> None:
        # UDP sessions and reverse flows whose sender summary is not present
        # carry no retransmit count — absence is not zero.
        assert last_session_retransmits(_session_doc(rx_bps=1e6)) is None
        assert last_session_retransmits("") is None

    def test_last_session_retransmits_distinguishes_zero_from_absent(self) -> None:
        assert last_session_retransmits(_session_doc(rx_bps=1e6, retransmits=0)) == 0

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
    port: int,
    mbps: float,
    *,
    stale_docs: int = 0,
    sender_retransmits: int | None = None,
    receiver_retransmits: int | None = None,
) -> tuple[ThroughputFlow, MagicMock, MagicMock]:
    """A flow over mocked capabilities; returns (flow, sender_mock, receiver_mock).

    The fake ``get_iperf_logs`` returns only the *stale* documents until the
    sender has been started, then appends the fresh session — mirroring the
    real sequencing (session completes only after the measurement window).
    """
    stale = "\n".join(_session_doc(rx_bps=1e6) for _ in range(stale_docs))
    fresh = stale + "\n" + _session_doc(rx_bps=mbps * 1e6, retransmits=receiver_retransmits)

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
        _session_doc(rx_bps=mbps * 1e6, retransmits=sender_retransmits)
        if sender.start_traffic_sender.called
        else ""
    )
    flow = ThroughputFlow(sender=sender, receiver=receiver, dest_host="192.168.32.3", port=port)
    return flow, sender, receiver


class TestMeasureConcurrentThroughput:
    def test_forward_flow_takes_retransmits_from_the_sending_client(self) -> None:
        flow, _, _ = _flow(5301, mbps=47.5, sender_retransmits=203, receiver_retransmits=99)
        results = measure_concurrent_throughput([flow], duration_s=10, sleep=lambda _s: None)
        # Our client sends, so its own log owns the loss count — never the
        # receiver's, whose summary describes the other direction.
        assert results[0].retransmits == 203

    def test_reverse_flow_takes_retransmits_from_the_remote_sender(self) -> None:
        flow, _, _ = _flow(5302, mbps=47.5, sender_retransmits=7, receiver_retransmits=1507)
        flow = replace(flow, reverse=True)
        results = measure_concurrent_throughput([flow], duration_s=10, sleep=lambda _s: None)
        # Under -R the REMOTE side sends the data, so the loss count belongs
        # to it — the local client sent nothing worth counting.
        assert results[0].retransmits == 1507

    def test_flow_without_a_sender_summary_reports_no_retransmits(self) -> None:
        flow, _, _ = _flow(5303, mbps=47.5)
        results = measure_concurrent_throughput([flow], duration_s=10, sleep=lambda _s: None)
        assert results[0].retransmits is None

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

        def _tx(
            host: str,
            port: int,
            time: int,
            bandwidth: int | None = None,
            reverse: bool = False,
            omit_s: int | None = None,
            json_output: bool = False,
            window: str | None = None,
        ) -> tuple[int, str]:
            order.append(
                f"tx:{host}:{port}:t={time}:b={bandwidth}:r={reverse}"
                f":o={omit_s}:j={json_output}:w={window}"
            )
            return (4001, "/tmp/tx.log")

        receiver.start_traffic_receiver.side_effect = _rx
        sender.start_traffic_sender.side_effect = _tx
        measure_concurrent_throughput([flow], duration_s=7, sleep=lambda _s: None)
        assert order == [
            "rx:5301",
            "tx:192.168.32.3:5301:t=7:b=None:r=False:o=None:j=True:w=None",
        ]

    def test_bandwidth_cap_passed_to_the_sender(self) -> None:
        base, sender, _ = _flow(5301, mbps=1.0)
        flow = ThroughputFlow(
            sender=base.sender,
            receiver=base.receiver,
            dest_host=base.dest_host,
            port=base.port,
            bandwidth_mbps=1,
        )
        measure_concurrent_throughput([flow], duration_s=3, sleep=lambda _s: None)
        assert sender.start_traffic_sender.call_args.kwargs["bandwidth"] == 1

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


class TestSenderOptionsAndRtt:
    def test_default_flow_sends_json_only(self) -> None:
        # --json is unconditional: the sender's own log is the forward-flow
        # RTT source, so it must always be machine-readable.
        flow, sender, _ = _flow(5301, mbps=5.0)
        measure_concurrent_throughput([flow], duration_s=10, sleep=lambda _s: None)
        kwargs = sender.start_traffic_sender.call_args.kwargs
        assert kwargs["json_output"] is True
        assert kwargs["reverse"] is False
        assert kwargs["omit_s"] is None
        assert kwargs["window"] is None
        assert "direction" not in kwargs  # the fragment seam is gone

    def test_reverse_flow_sets_reverse(self) -> None:
        base, sender, _ = _flow(5301, mbps=5.0)
        flow = ThroughputFlow(
            sender=base.sender,
            receiver=base.receiver,
            dest_host=base.dest_host,
            port=base.port,
            reverse=True,
        )
        measure_concurrent_throughput([flow], duration_s=10, sleep=lambda _s: None)
        assert sender.start_traffic_sender.call_args.kwargs["reverse"] is True

    def test_omit_passed_typed_and_extends_the_wait(self) -> None:
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
        assert sender.start_traffic_sender.call_args.kwargs["omit_s"] == 3
        assert sleeps.count(13.0) == 1

    def test_window_passed_to_the_sender(self) -> None:
        # Pinned socket buffer (-w): disables the receive-autotuning dip class
        # on high-BDP paths (live-diagnosed on a real overlay path).
        base, sender, _ = _flow(5301, mbps=5.0)
        flow = ThroughputFlow(
            sender=base.sender,
            receiver=base.receiver,
            dest_host=base.dest_host,
            port=base.port,
            window="8M",
        )
        measure_concurrent_throughput([flow], duration_s=10, sleep=lambda _s: None)
        assert sender.start_traffic_sender.call_args.kwargs["window"] == "8M"

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


# --- rated-path measurement: probe + sequential directions + convergence ------


def _fake_measure(probe=(0.5, 0.6), upload=(940.0, (20.0, 24.0)), download=(930.0, (21.0, 25.0))):
    """A measure() stub keyed on flow shape: capped→probe, reverse→download."""
    calls: list[tuple[ThroughputFlow, int]] = []

    def _fn(flows, *, duration_s, **_kw):
        (flow,) = flows
        calls.append((flow, duration_s))
        if flow.bandwidth_mbps is not None:
            return [
                FlowThroughput(port=flow.port, mbps=1.0, min_rtt_ms=probe[0], mean_rtt_ms=probe[1])
            ]
        mbps, rtt = download if flow.reverse else upload
        return [FlowThroughput(port=flow.port, mbps=mbps, min_rtt_ms=rtt[0], mean_rtt_ms=rtt[1])]

    return _fn, calls


class TestMeasurePathRtt:
    def test_builds_capped_probe_and_returns_rtt_pair(self) -> None:
        measure, calls = _fake_measure(probe=(0.7, 0.9))
        got = measure_path_rtt(
            MagicMock(), MagicMock(), "10.0.0.9", 5401, rate_mbps=2, duration_s=4, measure=measure
        )
        assert got == (0.7, 0.9)
        (flow, duration_s) = calls[0]
        assert flow.bandwidth_mbps == 2 and flow.port == 5401 and duration_s == 4
        assert flow.reverse is False and flow.dest_host == "10.0.0.9"


class TestMeasureOneDirection:
    def test_forward_flow_shape(self) -> None:
        measure, calls = _fake_measure(upload=(500.0, (2.0, 3.0)))
        got = measure_one_direction(
            MagicMock(),
            MagicMock(),
            "10.0.0.9",
            5402,
            reverse=False,
            duration_s=10,
            omit_s=3,
            measure=measure,
        )
        assert got.mbps == 500.0
        (flow, duration_s) = calls[0]
        assert flow.reverse is False and flow.omit_s == 3 and duration_s == 10
        assert flow.bandwidth_mbps is None  # saturating, not capped

    def test_reverse_flow_shape(self) -> None:
        measure, calls = _fake_measure(download=(450.0, (2.0, 3.0)))
        got = measure_one_direction(
            MagicMock(), MagicMock(), "10.0.0.9", 5403, reverse=True, measure=measure
        )
        assert got.mbps == 450.0
        assert calls[0][0].reverse is True

    def test_measure_one_direction_pins_window_on_the_flow(self) -> None:
        captured: list[ThroughputFlow] = []

        def _measure(flows, **_kw):  # type: ignore[no-untyped-def]
            captured.extend(flows)
            return [FlowThroughput(port=f.port, mbps=800.0) for f in flows]

        measure_one_direction(
            MagicMock(),
            MagicMock(),
            "10.1.30.50",
            5401,
            reverse=True,
            window="8M",
            measure=_measure,
        )
        assert [f.window for f in captured] == ["8M"]


def _ports_from(start: int = 5401):
    counter = iter(range(start, start + 1000))
    return lambda: next(counter)


class TestMeasurePathUntil:
    _DIRS = (
        DirectionSpec("upload", reverse=False),
        DirectionSpec("download", reverse=True),
    )

    def _run(self, stop_when, **kw):
        defaults = dict(
            sender=MagicMock(),
            receiver=MagicMock(),
            dest_host="10.0.0.9",
            directions=self._DIRS,
            allocate_port=_ports_from(),
            stop_when=stop_when,
            budget_s=180,
            monotonic=lambda: 0.0,
        )
        defaults.update(kw)
        return measure_path_until(**defaults)

    def test_stops_when_stop_when_returns_true_and_reports_findings(self) -> None:
        # stop after the caller has collected 2 rounds — the op reports both,
        # in order, and never judges them.
        measure, calls = _fake_measure()
        findings = self._run(lambda rounds: len(rounds) >= 2, measure=measure)
        assert isinstance(findings, list)
        assert [type(f).__name__ for f in findings] == ["PathMeasurement"] * 2
        assert findings[0].by_direction["download"].mbps == 930.0
        # 2 rounds x (probe + 2 directions) = 6 flows, distinct ports; each
        # round's first flow is the rate-capped probe, the rest saturate.
        ports = [flow.port for flow, _ in calls]
        assert len(ports) == 6 and len(set(ports)) == 6
        assert [flow.bandwidth_mbps for flow, _ in calls] == [1, None, None] * 2
        assert [flow.reverse for flow, _ in calls] == [False, False, True] * 2

    def test_stops_on_the_first_round_when_asked(self) -> None:
        measure, calls = _fake_measure()
        findings = self._run(lambda _rounds: True, measure=measure)
        assert len(findings) == 1
        assert len(calls) == 3  # exactly one round of flows

    def test_runs_to_budget_when_never_told_to_stop(self) -> None:
        measure, _ = _fake_measure()
        # deadline init (0) -> 150; round-1 check (0) < 150 continues; round-2
        # check (200) >= 150 stops. Two rounds ran, both reported.
        clock = iter([0.0, 0.0, 200.0])
        findings = self._run(
            lambda _rounds: False,  # never settled per the caller
            measure=measure,
            budget_s=150,
            monotonic=lambda: next(clock),
        )
        assert len(findings) == 2

    def test_stop_when_terminal_exception_propagates_without_retry(self) -> None:
        measure, calls = _fake_measure(probe=(None, None))

        def _stop_when(_rounds):
            raise AssertionError("no TCP-RTT samples")

        with pytest.raises(AssertionError, match="no TCP-RTT samples"):
            self._run(_stop_when, measure=measure)
        assert len(calls) == 3  # exactly one round ran; no retry

    def test_on_round_called_for_every_round_in_order(self) -> None:
        measure, _ = _fake_measure()
        seen: list[PathMeasurement] = []
        findings = self._run(lambda rounds: len(rounds) >= 3, measure=measure, on_round=seen.append)
        assert len(seen) == 3
        assert seen == findings  # same objects, same order
        assert all(isinstance(f, PathMeasurement) for f in seen)

    def test_stop_when_receives_the_growing_findings_list(self) -> None:
        # The predicate sees every round so far — it can look back N rounds to
        # implement a consecutive-pass policy without the op knowing about it.
        measure, _ = _fake_measure()
        lengths: list[int] = []

        def _stop_when(rounds):
            lengths.append(len(rounds))
            return len(rounds) >= 3

        self._run(_stop_when, measure=measure)
        assert lengths == [1, 2, 3]

    def test_measure_path_until_windows_directions_but_not_the_probe(self) -> None:
        captured: list[ThroughputFlow] = []

        def _measure(flows, **_kw):  # type: ignore[no-untyped-def]
            captured.extend(flows)
            return [FlowThroughput(port=f.port, mbps=800.0) for f in flows]

        ports = iter(range(5401, 5410))
        measure_path_until(
            sender=MagicMock(),
            receiver=MagicMock(),
            dest_host="10.1.30.50",
            directions=[DirectionSpec("upload", reverse=False)],
            allocate_port=lambda: next(ports),
            stop_when=lambda findings: True,
            budget_s=60.0,
            window="8M",
            measure=_measure,
        )
        # Round = probe flow first, then the direction flow.
        probe, direction = captured
        assert probe.bandwidth_mbps == DEFAULT_PROBE_RATE_MBPS
        assert probe.window is None  # probes stay unpinned
        assert direction.window == "8M"  # saturating flows are pinned


# --- external-endpoint measurement (client-log-only) ----------------------------


def _ext_sender(
    mbps: float = 800.0,
    rtt_us: list[tuple[float, float]] | None = None,
    error: str | None = None,
    complete: bool = True,
    retransmits: int | None = None,
) -> MagicMock:
    """A fake IperfClient whose --json log appears once the sender started."""
    if error is not None:
        doc = json.dumps({"start": {}, "error": error})
    elif complete:
        doc = _session_doc(rx_bps=mbps * 1e6, rtt_us=rtt_us, retransmits=retransmits)
    else:
        doc = '{"start": {"test_start"'  # forever-incomplete document
    sender = MagicMock()
    sender.start_traffic_sender.return_value = (777, "/tmp/ext_client.log")
    sender.get_iperf_logs.side_effect = lambda _log: (
        doc if sender.start_traffic_sender.called else ""
    )
    return sender


class TestLastSessionError:
    def test_reads_error_of_last_document(self) -> None:
        text = _session_doc(rx_bps=1e6) + "\n" + json.dumps({"error": "the server is busy"})
        assert last_session_error(text) == "the server is busy"

    def test_none_without_error_or_documents(self) -> None:
        assert last_session_error("") is None
        assert last_session_error(_session_doc(rx_bps=1e6)) is None


class TestMeasureExternalFlow:
    def test_forward_flow_reports_sender_retransmits_beside_the_rate(self) -> None:
        sender = _ext_sender(mbps=588.0, retransmits=688)
        result = measure_external_flow(
            ExternalFlow(sender=sender, dest_host="203.0.113.10", port=5201),
            duration_s=10,
            sleep=lambda _s: None,
        )
        assert result.mbps == pytest.approx(588.0)
        assert result.retransmits == 688

    def test_flow_without_a_sender_summary_reports_no_retransmits(self) -> None:
        sender = _ext_sender(mbps=875.0)
        result = measure_external_flow(
            ExternalFlow(sender=sender, dest_host="203.0.113.10", port=5201),
            duration_s=10,
            sleep=lambda _s: None,
        )
        assert result.retransmits is None

    def test_forward_flow_rate_and_rtt_from_client_log(self) -> None:
        sender = _ext_sender(mbps=875.0, rtt_us=[(480.0, 1250.0)])
        result = measure_external_flow(
            ExternalFlow(sender=sender, dest_host="203.0.113.10", port=5201),
            duration_s=10,
            sleep=lambda _s: None,
        )
        assert result.mbps == pytest.approx(875.0)
        assert result.min_rtt_ms == pytest.approx(0.48)
        assert result.mean_rtt_ms == pytest.approx(1.25)
        kwargs = sender.start_traffic_sender.call_args.kwargs
        assert sender.start_traffic_sender.call_args.args == ("203.0.113.10", 5201)
        assert kwargs["json_output"] is True
        assert kwargs["time"] == 10
        assert kwargs["reverse"] is False
        sender.stop_traffic.assert_called_once_with(777)

    def test_reverse_flow_reports_no_rtt_even_when_log_carries_samples(self) -> None:
        sender = _ext_sender(mbps=640.0, rtt_us=[(480.0, 1250.0)])
        result = measure_external_flow(
            ExternalFlow(sender=sender, dest_host="203.0.113.10", port=5202, reverse=True),
            duration_s=10,
            sleep=lambda _s: None,
        )
        assert result.mbps == pytest.approx(640.0)
        assert result.min_rtt_ms is None
        assert result.mean_rtt_ms is None
        assert sender.start_traffic_sender.call_args.kwargs["reverse"] is True

    def test_parallel_window_and_omit_passed_through_typed(self) -> None:
        sender = _ext_sender()
        measure_external_flow(
            ExternalFlow(
                sender=sender,
                dest_host="203.0.113.10",
                port=5203,
                parallel=5,
                window="4M",
                omit_s=3,
            ),
            duration_s=10,
            sleep=lambda _s: None,
        )
        kwargs = sender.start_traffic_sender.call_args.kwargs
        assert kwargs["parallel"] == 5
        assert kwargs["window"] == "4M"
        assert kwargs["omit_s"] == 3

    def test_endpoint_error_document_raises_with_reason_and_stops_sender(self) -> None:
        sender = _ext_sender(error="the server is busy running a test. try again later")
        with pytest.raises(RuntimeError, match="server is busy"):
            measure_external_flow(
                ExternalFlow(sender=sender, dest_host="203.0.113.10", port=5204),
                duration_s=10,
                sleep=lambda _s: None,
            )
        sender.stop_traffic.assert_called_once_with(777)

    def test_never_completing_log_raises_after_timeout_and_stops_sender(self) -> None:
        sender = _ext_sender(complete=False)
        clock = iter(float(t) for t in range(0, 400, 5))
        with pytest.raises(RuntimeError, match="no completed client-side result"):
            measure_external_flow(
                ExternalFlow(sender=sender, dest_host="203.0.113.10", port=5205),
                duration_s=10,
                result_timeout_s=30.0,
                sleep=lambda _s: None,
                monotonic=lambda: next(clock),
            )
        sender.stop_traffic.assert_called_once_with(777)

    def test_stop_traffic_errors_do_not_mask_the_result(self) -> None:
        sender = _ext_sender(mbps=500.0)
        sender.stop_traffic.side_effect = ConnectionError("device gone")
        result = measure_external_flow(
            ExternalFlow(sender=sender, dest_host="203.0.113.10", port=5206),
            duration_s=10,
            sleep=lambda _s: None,
        )
        assert result.mbps == pytest.approx(500.0)


class TestMeasureExternalPathUntil:
    def _run(
        self,
        stop_when,  # type: ignore[no-untyped-def]
        *,
        parallel: int | None = 5,
        window: str | None = None,
        budget_s: float = 600.0,
        on_round=None,  # type: ignore[no-untyped-def]
    ) -> tuple[list[PathMeasurement], list[ExternalFlow]]:
        captured: list[ExternalFlow] = []

        def _measure(flow: ExternalFlow, *, duration_s: int) -> FlowThroughput:
            captured.append(flow)
            rtt = (0.5, 0.7) if flow.bandwidth_mbps else (None, None)
            return FlowThroughput(port=flow.port, mbps=930.0, min_rtt_ms=rtt[0], mean_rtt_ms=rtt[1])

        ports = iter(range(5201, 5261))
        findings = measure_external_path_until(
            sender=MagicMock(),
            dest_host="203.0.113.10",
            directions=[
                DirectionSpec("upload", reverse=False),
                DirectionSpec("download", reverse=True),
            ],
            allocate_port=lambda: next(ports),
            stop_when=stop_when,
            budget_s=budget_s,
            parallel=parallel,
            window=window,
            on_round=on_round,
            measure_flow=_measure,
        )
        return findings, captured

    def test_round_shape_probe_then_directions_with_parallel_on_directions_only(
        self,
    ) -> None:
        findings, captured = self._run(lambda f: True, parallel=5, window="4M")
        assert len(findings) == 1
        probe, upload, download = captured
        assert probe.bandwidth_mbps == DEFAULT_PROBE_RATE_MBPS
        assert probe.parallel is None  # the probe is always a single stream
        assert probe.window is None  # and never pinned
        assert probe.reverse is False  # forward: client-side RTT observable
        assert upload.parallel == 5
        assert upload.window == "4M"
        assert upload.reverse is False
        assert download.reverse is True
        assert findings[0].probe_min_rtt_ms == pytest.approx(0.5)
        assert set(findings[0].by_direction) == {"upload", "download"}
        # Every flow drew a fresh port from the allocator.
        assert len({f.port for f in captured}) == 3

    def test_repeats_until_stop_when_and_reports_all_rounds(self) -> None:
        findings, captured = self._run(lambda f: len(f) >= 3)
        assert len(findings) == 3
        assert len(captured) == 9  # 3 rounds x (probe + 2 directions)

    def test_budget_stops_the_loop(self) -> None:
        clock = iter([0.0, 700.0, 800.0, 900.0])
        captured: list[ExternalFlow] = []

        def _measure(flow: ExternalFlow, *, duration_s: int) -> FlowThroughput:
            captured.append(flow)
            return FlowThroughput(port=flow.port, mbps=100.0)

        findings = measure_external_path_until(
            sender=MagicMock(),
            dest_host="203.0.113.10",
            directions=[DirectionSpec("upload", reverse=False)],
            allocate_port=lambda: 5201,
            stop_when=lambda f: False,
            budget_s=600.0,
            measure_flow=_measure,
            monotonic=lambda: next(clock),
        )
        assert len(findings) == 1  # the first post-round check saw the budget spent

    def test_on_round_called_per_round_and_terminal_stop_when_propagates(self) -> None:
        seen: list[PathMeasurement] = []

        def _stop(findings: list[PathMeasurement]) -> bool:
            if len(findings) == 2:
                raise AssertionError("terminal condition")
            return False

        with pytest.raises(AssertionError, match="terminal condition"):
            self._run(_stop, on_round=seen.append)
        assert len(seen) == 2


class TestExternalFlowNonCompletion:
    def test_endpoint_error_document_surfaces_as_endpoint_nonc(self) -> None:
        sender = _ext_sender(error="the server is busy running a test. try again later")
        with pytest.raises(NonCompletion) as ei:
            measure_external_flow(
                ExternalFlow(sender=sender, dest_host="203.0.113.10", port=5201),
                duration_s=10,
                sleep=lambda _s: None,
            )
        assert ei.value.which_side == "endpoint"
        assert ei.value.what == "error_document"
        assert "busy running a test" in ei.value.detail
        assert ei.value.port == 5201

    def test_a_stall_surfaces_as_unknown_no_completed_session(self) -> None:
        sender = _ext_sender(complete=False)
        with pytest.raises(NonCompletion) as ei:
            measure_external_flow(
                ExternalFlow(sender=sender, dest_host="203.0.113.10", port=5207),
                duration_s=1,
                sleep=lambda _s: None,
                result_timeout_s=0.0,
            )
        assert ei.value.which_side == "unknown"
        assert ei.value.what == "no_completed_session"
        assert ei.value.port == 5207


class TestExternalRetryWhen:
    def _run(self, flow_results, retry_when, on_retry=None, clock=None):  # type: ignore[no-untyped-def]
        calls: list[int] = []

        def _measure(flow, *, duration_s):
            calls.append(flow.port)
            r = flow_results.pop(0)
            if isinstance(r, Exception):
                raise r
            return FlowThroughput(port=flow.port, mbps=r)

        ports = iter(range(5201, 5261))
        findings = measure_external_path_until(
            sender=MagicMock(),
            dest_host="203.0.113.10",
            directions=[DirectionSpec("upload", reverse=False)],
            allocate_port=lambda: next(ports),
            stop_when=lambda f: True,
            budget_s=600.0,
            measure_flow=_measure,
            monotonic=clock or (lambda: 0.0),
            sleep=lambda _s: None,
            retry_when=retry_when,
            on_retry=on_retry,
        )
        return findings, calls

    def _nonc(self):
        return NonCompletion(which_side="endpoint", what="error_document", detail="busy", port=0)

    def test_predicate_true_redraws_on_next_port(self) -> None:
        _, calls = self._run([self._nonc(), 1.0, 900.0], retry_when=lambda f: True)
        assert calls == [5201, 5202, 5203]

    def test_predicate_false_raises_immediately(self) -> None:
        with pytest.raises(NonCompletion):
            self._run([self._nonc()], retry_when=lambda f: False)

    def test_default_none_never_retries(self) -> None:
        with pytest.raises(NonCompletion):
            self._run([self._nonc()], retry_when=None)

    def test_budget_exhaustion_raises_even_if_predicate_says_yes(self) -> None:
        clock = iter([0.0, 700.0, 800.0, 900.0, 1000.0])
        with pytest.raises(NonCompletion):
            self._run(
                [self._nonc(), self._nonc()], retry_when=lambda f: True, clock=lambda: next(clock)
            )

    def test_on_retry_fires_once_per_absorbed_redraw_only(self) -> None:
        seen: list[int] = []
        self._run(
            [self._nonc(), 1.0, 900.0],
            retry_when=lambda f: True,
            on_retry=lambda exc, port: seen.append(port),
        )
        assert seen == [5201]

    def test_a_path_statement_is_still_not_retried(self) -> None:
        # guard: a predicate that returns False for a non-refusal fails honestly
        nonc = NonCompletion(
            which_side="endpoint", what="error_document", detail="access denied", port=0
        )
        with pytest.raises(NonCompletion):
            self._run([nonc], retry_when=lambda f: "denied" not in f.detail)


# --- NonCompletion -------------------------------------------------------


class TestConcurrentNonCompletion:
    def test_receiver_no_show_is_local_receiver(self) -> None:
        flow, _, receiver = _flow(5301, mbps=10.0)
        receiver.get_iperf_logs.side_effect = lambda _log: ""
        with pytest.raises(NonCompletion) as ei:
            measure_concurrent_throughput(
                [flow],
                duration_s=10,
                sleep=lambda _s: None,
                result_timeout_s=0.0,
            )
        assert ei.value.which_side == "local_receiver"
        assert ei.value.what == "no_completed_session"
        assert ei.value.port == 5301

    def test_reverse_flow_sender_no_show_is_also_local_receiver(self) -> None:
        # the initiating (data-receiving) side is OUR rig — never external
        flow, sender, _receiver = _flow(5302, mbps=10.0)
        flow = replace(flow, reverse=True)
        sender.get_iperf_logs.side_effect = lambda _log: ""  # our side never completes
        with pytest.raises(NonCompletion) as ei:
            measure_concurrent_throughput(
                [flow],
                duration_s=10,
                sleep=lambda _s: None,
                result_timeout_s=0.0,
            )
        assert ei.value.which_side == "local_receiver"


class TestNonCompletion:
    def test_carries_provenance_fields_and_is_a_runtime_error(self) -> None:
        f = NonCompletion(
            which_side="endpoint",
            what="error_document",
            detail="the server is busy running a test",
            port=5201,
        )
        assert isinstance(f, RuntimeError)  # catchable at the caller's RuntimeError seam
        assert f.which_side == "endpoint"
        assert f.what == "error_document"
        assert f.port == 5201
        assert "busy running a test" in str(f)  # detail survives into the message
