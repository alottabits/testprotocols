"""Tests for testoperations.iperf_client module."""

from __future__ import annotations

from unittest.mock import MagicMock

from testoperations.iperf_client import sender_life_record, start_iperf

# ---------------------------------------------------------------------------
# start_iperf
# ---------------------------------------------------------------------------


class TestStartIperf:
    def test_starts_receiver_and_sender(self) -> None:
        client = MagicMock()
        server = MagicMock()

        start_iperf(client, server, port=5001)

        server.start_receiver.assert_called_once()
        client.start_sender.assert_called_once()

    def test_returns_dict_with_pids_and_logs(self) -> None:
        client = MagicMock()
        server = MagicMock()
        client.start_sender.return_value = ("pid_s", "log_s.txt")
        server.start_receiver.return_value = ("pid_r", "log_r.txt")

        result = start_iperf(client, server, port=5001)

        assert result["sender_pid"] == "pid_s"
        assert result["sender_log"] == "log_s.txt"
        assert result["receiver_pid"] == "pid_r"
        assert result["receiver_log"] == "log_r.txt"

    def test_passes_port_and_options(self) -> None:
        client = MagicMock()
        server = MagicMock()

        start_iperf(client, server, port=5201, time=30, udp=True, ip_version=6)

        server.start_receiver.assert_called_once_with(5201, time=30, udp=True, ip_version=6)
        client.start_sender.assert_called_once_with(5201, time=30, udp=True, ip_version=6)

    def test_handles_non_tuple_return(self) -> None:
        client = MagicMock()
        server = MagicMock()
        client.start_sender.return_value = "raw_pid"
        server.start_receiver.return_value = "raw_pid_r"

        result = start_iperf(client, server, port=5001)

        assert result["sender_pid"] == "raw_pid"
        assert result["sender_log"] is None
        assert result["receiver_pid"] == "raw_pid_r"
        assert result["receiver_log"] is None


# ---------------------------------------------------------------------------
# sender_life_record
# ---------------------------------------------------------------------------

IPERF3_LOG = """\
Connecting to host 198.51.100.9, port 5201
[  5] local 10.1.30.50 port 47000 connected to 198.51.100.9 port 5201
[ ID] Interval           Transfer     Bitrate
[  5]   0.00-1.00   sec  1.25 MBytes  10.5 Mbits/sec
[  5]   1.00-2.00   sec  1.25 MBytes  10.5 Mbits/sec
[  5]   2.00-3.00   sec  1.25 MBytes  10.5 Mbits/sec
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate
[  5]   0.00-3.00   sec  3.75 MBytes  10.5 Mbits/sec                  sender
"""

IPERF2_GAPPY_LOG = """\
[  3] local 10.1.30.51 port 51000 connected with 198.51.100.4 port 5001
[ ID] Interval       Transfer     Bandwidth
[  3]  0.0- 1.0 sec  128 KBytes  1.05 Mbits/sec
[  3]  1.0- 2.0 sec  128 KBytes  1.05 Mbits/sec
[  3]  4.0- 5.0 sec  128 KBytes  1.05 Mbits/sec
[  3]  0.0- 5.0 sec  384 KBytes  0.63 Mbits/sec
"""


class TestSenderLifeRecord:
    def test_counts_intervals_and_excludes_summary(self) -> None:
        client = MagicMock()
        client.get_iperf_logs.return_value = IPERF3_LOG

        record = sender_life_record(client, "sender.log")

        client.get_iperf_logs.assert_called_once_with("sender.log")
        assert record.intervals == 3
        assert record.gaps == ()
        assert record.total_bytes == 3 * int(1.25 * 1024**2)

    def test_detects_gap_between_intervals(self) -> None:
        client = MagicMock()
        client.get_iperf_logs.return_value = IPERF2_GAPPY_LOG

        record = sender_life_record(client, "sender.log")

        assert record.intervals == 3
        assert record.gaps == ((2.0, 4.0),)

    def test_no_interval_lines_is_no_recorded_life(self) -> None:
        client = MagicMock()
        client.get_iperf_logs.return_value = "connect failed: No route to host\n"

        record = sender_life_record(client, "sender.log")

        assert record.intervals == 0
        assert record.gaps == ()
        assert record.total_bytes == 0

    def test_gap_tolerance_suppresses_small_holes(self) -> None:
        client = MagicMock()
        client.get_iperf_logs.return_value = IPERF2_GAPPY_LOG

        record = sender_life_record(client, "sender.log", gap_tolerance_s=2.5)

        assert record.gaps == ()
