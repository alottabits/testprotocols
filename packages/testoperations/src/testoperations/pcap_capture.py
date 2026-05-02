"""Packet capture operations — context manager wrapping tcpdump lifecycle.

Receives a resolved ``pcap`` template instance from the caller.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from testprotocols.pcap_capture import PcapCapture


@contextmanager
def tcpdump(
    pcap_capture: Any,
    fname: str,
    interface: str,
    filters: str | None = None,
) -> Generator[None, None, None]:
    """Context manager that starts a tcpdump capture and stops it on exit.

    The capture is written to *fname* on the device.  An optional BPF *filters*
    string is forwarded to the underlying template.

    *pcap_capture* is typed ``Any`` because the existing call shape passes
    arguments that do not match the :class:`PcapCapture` protocol's
    ``start_tcpdump`` signature (filters is forwarded as a BPF string while the
    protocol expects ``dict[str, Any] | None``). Pre-existing tech debt; logic
    is not modified here.
    """
    if filters is not None:
        pcap_capture.start_tcpdump(fname, interface, filters=filters)
    else:
        pcap_capture.start_tcpdump(fname, interface)
    try:
        yield
    finally:
        pcap_capture.stop_tcpdump(fname)


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
