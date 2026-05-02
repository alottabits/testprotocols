"""Pcap / Capture template.

Defines the abstract contract for packet capture operations using
tcpdump and tshark.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PcapCapture(Protocol):
    """Abstract contract for packet capture operations."""

    def start_tcpdump(
        self,
        interface: str,
        port: str | None,
        output_file: str = "pkt_capture.pcap",
        filters: dict | None = None,
        additional_filters: str | None = "",
    ) -> str:
        """Start a tcpdump capture on *interface* and return the process identifier."""
        ...

    def stop_tcpdump(self, process_id: str) -> None:
        """Stop the tcpdump process identified by *process_id*."""
        ...

    def tshark_read_pcap(
        self,
        fname: str,
        additional_args: str | None = None,
        timeout: int = 30,
        rm_pcap: bool = False,
    ) -> str:
        """Read and parse pcap file *fname* using tshark and return the output."""
        ...
