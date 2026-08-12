"""Tests for testoperations._capture — the family's shared primitives."""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import MagicMock, patch

from testoperations._capture import capture_shared_window, read_fields


def _pcap(tshark_output: str = "") -> MagicMock:
    pcap = MagicMock()
    pcap.start_tcpdump.return_value = "pid-1"
    pcap.tshark_read_pcap.return_value = tshark_output
    return pcap


class TestCaptureSharedWindow:
    def test_all_starts_precede_any_stop(self) -> None:
        calls: list[str] = []

        def _record(event: str, result: str | None = None) -> Callable[..., str | None]:
            def _side_effect(*args: object, **kwargs: object) -> str | None:
                calls.append(event)
                return result

            return _side_effect

        one, two = _pcap(), _pcap()
        one.start_tcpdump.side_effect = _record("start1", "p1")
        two.start_tcpdump.side_effect = _record("start2", "p2")
        one.stop_tcpdump.side_effect = _record("stop1")
        two.stop_tcpdump.side_effect = _record("stop2")

        capture_shared_window([(one, "n0", "/tmp/a.pcap"), (two, "n0", "/tmp/b.pcap")], window_s=0)

        assert calls.index("start1") < calls.index("stop1")
        assert calls.index("start2") < calls.index("stop1")
        assert calls.index("start2") < calls.index("stop2")

    def test_single_vantage_is_the_n1_case(self) -> None:
        pcap = _pcap()
        capture_shared_window([(pcap, "north0", "/tmp/x.pcap")], window_s=0)
        pcap.start_tcpdump.assert_called_once_with("north0", None, output_file="/tmp/x.pcap")
        pcap.stop_tcpdump.assert_called_once_with("pid-1")

    def test_started_captures_stopped_even_if_wait_interrupted(self) -> None:
        one, two = _pcap(), _pcap()
        with patch("testoperations._capture.time.sleep", side_effect=KeyboardInterrupt):
            try:
                capture_shared_window(
                    [(one, "n0", "/tmp/a.pcap"), (two, "n0", "/tmp/b.pcap")], window_s=1
                )
            except KeyboardInterrupt:
                pass
        one.stop_tcpdump.assert_called_once()
        two.stop_tcpdump.assert_called_once()


class TestReadFields:
    def test_one_read_per_entry_with_filter_and_fields(self) -> None:
        pcap = _pcap("1200\n")
        read_fields(
            pcap,
            "/tmp/x.pcap",
            [("frame.len>=100", "-T fields -e frame.len"), ("udp", "-T fields -e frame.len")],
        )
        first, second = pcap.tshark_read_pcap.call_args_list
        assert first.args[0] == "/tmp/x.pcap"
        assert first.kwargs["additional_args"] == '-Y "frame.len>=100" -T fields -e frame.len'
        assert second.kwargs["additional_args"] == '-Y "udp" -T fields -e frame.len'

    def test_capture_file_removed_on_the_last_read_only(self) -> None:
        pcap = _pcap("")
        read_fields(pcap, "/tmp/x.pcap", [("a", "-e f"), ("b", "-e f"), ("c", "-e f")])
        removals = [call.kwargs["rm_pcap"] for call in pcap.tshark_read_pcap.call_args_list]
        assert removals == [False, False, True]

    def test_removal_can_be_declined(self) -> None:
        pcap = _pcap("")
        read_fields(pcap, "/tmp/x.pcap", [("a", "-e f")], remove_on_last=False)
        assert pcap.tshark_read_pcap.call_args.kwargs["rm_pcap"] is False

    def test_returns_nonempty_lines_per_read(self) -> None:
        pcap = _pcap("18\n\n  \n46\n")
        (lines,) = read_fields(pcap, "/tmp/x.pcap", [("a", "-e f")])
        assert lines == ["18", "46"]
