"""Tests for testoperations.path_placement module."""

from __future__ import annotations

import time
from collections.abc import Callable
from unittest.mock import MagicMock, patch

from testoperations.path_placement import (
    ConvergenceRecord,
    SizeBand,
    await_stream_on_path,
    count_signature_on_path,
    locate_streams_by_size,
)

BAND = SizeBand(min_bytes=1180, max_bytes=1220)


def _pcap(tshark_output: str = "") -> MagicMock:
    pcap = MagicMock()
    pcap.start_tcpdump.return_value = "pid-1"
    pcap.tshark_read_pcap.return_value = tshark_output
    return pcap


# ---------------------------------------------------------------------------
# count_signature_on_path
# ---------------------------------------------------------------------------


class TestCountSignatureOnPath:
    def test_counts_nonempty_lines(self) -> None:
        pcap = _pcap("1200\n1198\n\n1210\n")

        count = count_signature_on_path(pcap, "north0", BAND, window_s=0)

        assert count == 3

    def test_zero_when_filter_matches_nothing(self) -> None:
        assert count_signature_on_path(_pcap(""), "north0", BAND, window_s=0) == 0

    def test_capture_lifecycle_and_band_filter(self) -> None:
        pcap = _pcap("1200\n")

        count_signature_on_path(pcap, "north0", BAND, window_s=0, capture_file="/tmp/x.pcap")

        pcap.start_tcpdump.assert_called_once_with("north0", None, output_file="/tmp/x.pcap")
        pcap.stop_tcpdump.assert_called_once_with("pid-1")
        args = pcap.tshark_read_pcap.call_args
        assert args.args[0] == "/tmp/x.pcap"
        assert "frame.len>=1180 and frame.len<=1220" in args.kwargs["additional_args"]
        assert args.kwargs["rm_pcap"] is True

    def test_capture_stopped_even_if_wait_interrupted(self) -> None:
        pcap = _pcap()
        with patch("testoperations.path_placement.time.sleep", side_effect=KeyboardInterrupt):
            try:
                count_signature_on_path(pcap, "north0", BAND, window_s=1)
            except KeyboardInterrupt:
                pass
        pcap.stop_tcpdump.assert_called_once_with("pid-1")


# ---------------------------------------------------------------------------
# locate_streams_by_size
# ---------------------------------------------------------------------------


class TestLocateStreamsBySize:
    def test_counts_every_signature_on_every_path(self) -> None:
        wan1, wan2 = _pcap("1200\n1201\n"), _pcap("")
        counts = locate_streams_by_size(
            paths={"wan1": wan1, "wan2": wan2},
            interfaces={"wan1": "north0", "wan2": "north0"},
            signatures={"governed": BAND, "control": SizeBand(700, 740)},
            window_s=0,
        )

        assert counts == {
            "wan1": {"governed": 2, "control": 2},
            "wan2": {"governed": 0, "control": 0},
        }

    def test_all_captures_start_before_any_stop(self) -> None:
        calls: list[str] = []

        def _record(event: str, result: str | None = None) -> Callable[..., str | None]:
            def _side_effect(*args: object, **kwargs: object) -> str | None:
                calls.append(event)
                return result

            return _side_effect

        wan1, wan2 = _pcap(), _pcap()
        wan1.start_tcpdump.side_effect = _record("start1", "p1")
        wan2.start_tcpdump.side_effect = _record("start2", "p2")
        wan1.stop_tcpdump.side_effect = _record("stop1")
        wan2.stop_tcpdump.side_effect = _record("stop2")

        locate_streams_by_size(
            paths={"wan1": wan1, "wan2": wan2},
            interfaces={"wan1": "n0", "wan2": "n0"},
            signatures={"s": BAND},
            window_s=0,
        )

        assert calls.index("start1") < calls.index("stop1")
        assert calls.index("start2") < calls.index("stop1")
        assert calls.index("start2") < calls.index("stop2")

    def test_distinct_capture_files_per_path(self) -> None:
        wan1, wan2 = _pcap(), _pcap()
        locate_streams_by_size(
            paths={"wan1": wan1, "wan2": wan2},
            interfaces={"wan1": "n0", "wan2": "n0"},
            signatures={"s": BAND},
            window_s=0,
            capture_dir="/tmp/caps",
        )
        f1 = wan1.start_tcpdump.call_args.kwargs["output_file"]
        f2 = wan2.start_tcpdump.call_args.kwargs["output_file"]
        assert f1 != f2
        assert f1.startswith("/tmp/caps/")


# ---------------------------------------------------------------------------
# await_stream_on_path
# ---------------------------------------------------------------------------


class TestAwaitStreamOnPath:
    def test_converges_when_signature_lands_on_expected_path(self) -> None:
        wan1, wan2 = _pcap("1200\n"), _pcap("")

        record = await_stream_on_path(
            paths={"wan1": wan1, "wan2": wan2},
            interfaces={"wan1": "n0", "wan2": "n0"},
            signature=BAND,
            expected_path="wan1",
            budget_s=5.0,
            anchor_monotonic=time.monotonic(),
            poll_s=0,
        )

        assert isinstance(record, ConvergenceRecord)
        assert record.converged is True
        assert record.samples[-1][1] == "wan1"
        assert record.elapsed_s >= 0.0

    def test_gives_up_after_budget_without_verdict(self) -> None:
        wan1, wan2 = _pcap(""), _pcap("1200\n")

        record = await_stream_on_path(
            paths={"wan1": wan1, "wan2": wan2},
            interfaces={"wan1": "n0", "wan2": "n0"},
            signature=BAND,
            expected_path="wan1",
            budget_s=0.0,
            anchor_monotonic=time.monotonic(),
            poll_s=0,
        )

        assert record.converged is False
        assert record.samples[-1][1] == "wan2"  # located, but not expected

    def test_elapsed_measured_from_caller_anchor(self) -> None:
        wan1 = _pcap("1200\n")

        record = await_stream_on_path(
            paths={"wan1": wan1},
            interfaces={"wan1": "n0"},
            signature=BAND,
            expected_path="wan1",
            budget_s=5.0,
            anchor_monotonic=time.monotonic() - 10.0,  # anchored 10 s ago
            poll_s=0,
        )

        assert record.elapsed_s >= 10.0

    def test_no_signature_anywhere_records_none(self) -> None:
        record = await_stream_on_path(
            paths={"wan1": _pcap(""), "wan2": _pcap("")},
            interfaces={"wan1": "n0", "wan2": "n0"},
            signature=BAND,
            expected_path="wan1",
            budget_s=0.0,
            anchor_monotonic=time.monotonic(),
            poll_s=0,
        )

        assert record.converged is False
        assert record.samples[0][1] is None
