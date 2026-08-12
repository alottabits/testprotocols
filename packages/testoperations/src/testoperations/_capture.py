"""Private capture-composition primitives for the capture-analysis family.

The family's shared mechanic, factored once: a shared observation window
(every capture started before any stops — what lets a multi-vantage caller
read presence-here/absence-there as one fact; a single vantage is the N=1
case of the same bracket) and the per-filter field read over a finished
capture file. Public operations (``path_placement``,
``marking_observation``) compose these; tshark field tokens and display
filters never appear in a public signature.
"""

from __future__ import annotations

import time
from collections.abc import Sequence

from testprotocols.pcap_capture import PcapCapture


def capture_shared_window(
    captures: Sequence[tuple[PcapCapture, str, str]],
    window_s: float,
) -> None:
    """Capture every ``(pcap, interface, capture_file)`` for ONE shared window.

    All starts precede the wait and all stops follow it — no capture stops
    before another starts, so every file describes the same observation
    window. The stops run in a ``finally`` so an interrupted wait still
    releases every started capture.
    """
    started: list[tuple[PcapCapture, str]] = []
    for pcap, interface, capture_file in captures:
        started.append((pcap, pcap.start_tcpdump(interface, None, output_file=capture_file)))
    try:
        time.sleep(window_s)
    finally:
        for pcap, process_id in started:
            pcap.stop_tcpdump(process_id)


def read_fields(
    pcap: PcapCapture,
    capture_file: str,
    reads: Sequence[tuple[str, str]],
    remove_on_last: bool = True,
) -> list[list[str]]:
    """One tshark read of *capture_file* per ``(display_filter, field_args)``.

    Returns the non-empty output lines per read, in order; the capture file
    is removed on the last read (the finished window has been fully
    consumed). Filter and field syntax stay the operations' private
    concern — callers of the public API never see them.
    """
    outputs: list[list[str]] = []
    for index, (display_filter, field_args) in enumerate(reads):
        last = index == len(reads) - 1
        out = pcap.tshark_read_pcap(
            capture_file,
            additional_args=f'-Y "{display_filter}" {field_args}',
            rm_pcap=remove_on_last and last,
        )
        outputs.append([line for line in out.splitlines() if line.strip()])
    return outputs
