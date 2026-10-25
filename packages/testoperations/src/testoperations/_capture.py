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
from dataclasses import dataclass

from testprotocols.pcap_capture import PcapCapture


@dataclass(frozen=True)
class CaptureSpec:
    """One capture of a shared window: start *pcap* on *interface*, into *capture_file*."""

    pcap: PcapCapture
    interface: str
    capture_file: str


@dataclass(frozen=True)
class FieldRead:
    """One tshark read of a finished capture: *display_filter* selects the frames,
    *field_args* names the fields to print."""

    display_filter: str
    field_args: str


def capture_shared_window(
    captures: Sequence[CaptureSpec],
    window_s: float,
) -> None:
    """Capture every :class:`CaptureSpec` for ONE shared window.

    All starts precede the wait and all stops follow it — no capture stops
    before another starts, so every file describes the same observation
    window. Every capture that started is stopped on every exit: a start
    that fails after others have started stops those (the window is not
    waited), an interrupted wait still releases every started capture, and
    a stop that raises does not skip the stops after it. The error of a
    failing start or wait propagates once every stop ran; a failing stop
    raises its own error (an ``ExceptionGroup`` when more than one stop
    failed).
    """
    started: list[tuple[PcapCapture, str]] = []
    try:
        for spec in captures:
            started.append(
                (
                    spec.pcap,
                    spec.pcap.start_tcpdump(spec.interface, None, output_file=spec.capture_file),
                )
            )
        time.sleep(window_s)
    finally:
        _stop_every(started)


def _stop_every(started: Sequence[tuple[PcapCapture, str]]) -> None:
    """Stop every started capture, continuing past a stop that raises."""
    failures: list[Exception] = []
    for pcap, process_id in started:
        try:
            pcap.stop_tcpdump(process_id)
        except Exception as exc:  # every later stop still runs
            failures.append(exc)
    if len(failures) == 1:
        raise failures[0]
    if failures:
        raise ExceptionGroup("stopping the shared capture window", failures)


def read_fields(
    pcap: PcapCapture,
    capture_file: str,
    reads: Sequence[FieldRead],
    remove_on_last: bool = True,
) -> list[list[str]]:
    """One tshark read of *capture_file* per :class:`FieldRead`.

    Returns the non-empty output lines per read, in order; the capture file
    is removed on the last read (the finished window has been fully
    consumed). Filter and field syntax stay the operations' private
    concern — callers of the public API never see them.
    """
    outputs: list[list[str]] = []
    for index, read in enumerate(reads):
        last = index == len(reads) - 1
        out = pcap.tshark_read_pcap(
            capture_file,
            additional_args=f'-Y "{read.display_filter}" {read.field_args}',
            rm_pcap=remove_on_last and last,
        )
        outputs.append([line for line in out.splitlines() if line.strip()])
    return outputs
