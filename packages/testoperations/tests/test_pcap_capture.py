"""Tests for testoperations.pcap_capture module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from testoperations.pcap_capture import read_tcpdump, tcpdump

# ---------------------------------------------------------------------------
# tcpdump (context manager)
# ---------------------------------------------------------------------------


class TestTcpdump:
    def test_starts_and_stops_tcpdump(self):
        pcap = MagicMock()
        with tcpdump(pcap, "capture.pcap", "eth0"):
            pcap.start_tcpdump.assert_called_once()
        pcap.stop_tcpdump.assert_called_once_with("capture.pcap")

    def test_stops_on_exception(self):
        pcap = MagicMock()
        with pytest.raises(RuntimeError):
            with tcpdump(pcap, "capture.pcap", "eth0"):
                raise RuntimeError("oops")
        pcap.stop_tcpdump.assert_called_once_with("capture.pcap")

    def test_passes_filters(self):
        pcap = MagicMock()
        with tcpdump(pcap, "capture.pcap", "eth0", filters="port 80"):
            pcap.start_tcpdump.assert_called_once_with("capture.pcap", "eth0", filters="port 80")

    def test_no_filters(self):
        pcap = MagicMock()
        with tcpdump(pcap, "capture.pcap", "eth0"):
            pcap.start_tcpdump.assert_called_once_with("capture.pcap", "eth0")


# ---------------------------------------------------------------------------
# read_tcpdump
# ---------------------------------------------------------------------------


class TestReadTcpdump:
    def test_delegates_to_pcap_tshark_read(self):
        pcap = MagicMock()
        pcap.tshark_read_pcap.return_value = "frame data"

        result = read_tcpdump(pcap, "capture.pcap")

        pcap.tshark_read_pcap.assert_called_once_with(
            "capture.pcap", additional_args="", rm_pcap=True
        )
        assert result == "frame data"

    def test_passes_opts_and_rm_pcap(self):
        pcap = MagicMock()
        read_tcpdump(pcap, "capture.pcap", opts="-T fields", rm_pcap=False)
        pcap.tshark_read_pcap.assert_called_once_with(
            "capture.pcap", additional_args="-T fields", rm_pcap=False
        )
