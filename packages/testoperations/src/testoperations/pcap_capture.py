"""Packet capture operations — context manager wrapping tcpdump lifecycle.

Receives a resolved ``pcap`` template instance from the caller.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from testprotocols.pcap_capture import PcapCapture


@contextmanager
def tcpdump(
    pcap_capture: PcapCapture,
    fname: str,
    interface: str,
    filters: str | None = None,
) -> Generator[None, None, None]:
    """Context manager that starts a tcpdump capture and stops it on exit.

    The capture is written to *fname* on the device. An optional BPF *filters* string is
    forwarded as the protocol's ``additional_filters``. The stop uses the process identifier
    the start returned.

    The released operation passed *fname* and *interface* in the wrong order for
    :meth:`~testprotocols.pcap_capture.PcapCapture.start_tcpdump` (``interface`` first, the
    file as ``output_file``) and stopped the capture by *fname*; it now makes the protocol's
    calls.
    """
    process_id = pcap_capture.start_tcpdump(
        interface, None, output_file=fname, additional_filters=filters or ""
    )
    try:
        yield
    finally:
        pcap_capture.stop_tcpdump(process_id)


def read_tcpdump(
    pcap_capture: PcapCapture,
    fname: str,
    opts: str = "",
    rm_pcap: bool = True,
) -> str:
    """Read a pcap file *fname* via tshark.

    *opts* is forwarded as additional tshark arguments.  If *rm_pcap* is True
    the pcap file is removed after reading.
    """
    return pcap_capture.tshark_read_pcap(fname, additional_args=opts, rm_pcap=rm_pcap)
