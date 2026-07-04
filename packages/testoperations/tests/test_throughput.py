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
    measure_concurrent_throughput,
)


def _session_doc(rx_bps: float | None = None, sum_bps: float | None = None) -> str:
    end: dict[str, dict[str, float]] = {}
    if rx_bps is not None:
        end["sum_received"] = {"bits_per_second": rx_bps}
    if sum_bps is not None:
        end["sum"] = {"bits_per_second": sum_bps}
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

        def _tx(host: str, port: int, time: int) -> tuple[int, str]:
            order.append(f"tx:{host}:{port}:t={time}")
            return (4001, "/tmp/tx.log")

        receiver.start_traffic_receiver.side_effect = _rx
        sender.start_traffic_sender.side_effect = _tx
        measure_concurrent_throughput([flow], duration_s=7, sleep=lambda _s: None)
        assert order == ["rx:5301", "tx:192.168.32.3:5301:t=7"]

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
