"""Tests for testoperations.iperf_client module."""

from __future__ import annotations

from unittest.mock import MagicMock

from testoperations.iperf_client import start_iperf

# ---------------------------------------------------------------------------
# start_iperf
# ---------------------------------------------------------------------------


class TestStartIperf:
    def test_starts_receiver_and_sender(self):
        client = MagicMock()
        server = MagicMock()

        start_iperf(client, server, port=5001)

        server.start_receiver.assert_called_once()
        client.start_sender.assert_called_once()

    def test_returns_dict_with_pids_and_logs(self):
        client = MagicMock()
        server = MagicMock()
        client.start_sender.return_value = ("pid_s", "log_s.txt")
        server.start_receiver.return_value = ("pid_r", "log_r.txt")

        result = start_iperf(client, server, port=5001)

        assert result["sender_pid"] == "pid_s"
        assert result["sender_log"] == "log_s.txt"
        assert result["receiver_pid"] == "pid_r"
        assert result["receiver_log"] == "log_r.txt"

    def test_passes_port_and_options(self):
        client = MagicMock()
        server = MagicMock()

        start_iperf(client, server, port=5201, time=30, udp=True, ip_version=6)

        server.start_receiver.assert_called_once_with(5201, time=30, udp=True, ip_version=6)
        client.start_sender.assert_called_once_with(5201, time=30, udp=True, ip_version=6)

    def test_handles_non_tuple_return(self):
        client = MagicMock()
        server = MagicMock()
        client.start_sender.return_value = "raw_pid"
        server.start_receiver.return_value = "raw_pid_r"

        result = start_iperf(client, server, port=5001)

        assert result["sender_pid"] == "raw_pid"
        assert result["sender_log"] is None
        assert result["receiver_pid"] == "raw_pid_r"
        assert result["receiver_log"] is None
