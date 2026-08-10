"""Wire-vantage stream placement by packet-size signature.

Receives resolved ``pcap`` template instances from the caller — one per
candidate path (a capture point on each wire a flow could ride, e.g. an
impairment bridge per WAN uplink). Encrypted transport hides a flow's inner
addressing at every wire vantage, so streams are told apart by a declared
**packet-size signature**: each stream is driven at a distinct frame size,
encapsulation adds bounded overhead, and the separation survives on the
wire. These operations capture, count and locate; deciding what a count
*means* (placed here, absent there, converged in budget) stays with the
caller — operations are assertion-free.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass

from testprotocols.pcap_capture import PcapCapture


@dataclass(frozen=True)
class SizeBand:
    """Inclusive on-the-wire frame-length band identifying one stream."""

    min_bytes: int
    max_bytes: int


@dataclass(frozen=True)
class ConvergenceRecord:
    """Recorded outcome of one bounded placement await (facts, no verdict).

    ``samples`` is the full observation trace: one ``(elapsed_s, located)``
    entry per poll, where ``elapsed_s`` counts from the caller's anchor and
    ``located`` names the path whose capture carried the signature in that
    poll (``None`` when no path did). ``elapsed_s`` is the anchor-relative
    time of the first sample that located the signature on the expected
    path — meaningful only when ``converged`` is True.
    """

    elapsed_s: float
    converged: bool
    samples: tuple[tuple[float, str | None], ...]


def _band_filter(signature: SizeBand) -> str:
    return f"frame.len>={signature.min_bytes} and frame.len<={signature.max_bytes}"


def count_signature_on_path(
    pcap: PcapCapture,
    interface: str,
    signature: SizeBand,
    window_s: float,
    capture_file: str = "/tmp/path_placement.pcap",
) -> int:
    """Capture *interface* for *window_s* and count frames inside *signature*.

    The shared counting primitive: a bounded capture at one wire vantage,
    read back through a frame-length display filter. Returns the frame
    count — a caller judging "this path carries the flow" interprets the
    count against its own floor (a known burst size, a rate, non-zero).
    """
    process_id = pcap.start_tcpdump(interface, None, output_file=capture_file)
    try:
        time.sleep(window_s)
    finally:
        pcap.stop_tcpdump(process_id)
    out = pcap.tshark_read_pcap(
        capture_file,
        additional_args=f'-Y "{_band_filter(signature)}" -T fields -e frame.len',
        rm_pcap=True,
    )
    return sum(1 for line in out.splitlines() if line.strip())


def locate_streams_by_size(
    paths: Mapping[str, PcapCapture],
    interfaces: Mapping[str, str],
    signatures: Mapping[str, SizeBand],
    window_s: float,
    capture_dir: str = "/tmp",
) -> dict[str, dict[str, int]]:
    """Capture every path in one shared window; count every signature on each.

    All captures are started before any stops, so every count describes the
    same observation window — what lets a caller read "present on one path,
    absent on the other" as one fact rather than two moments. Returns
    ``{path: {stream: frame_count}}``; the placement judgment (which counts
    constitute presence) stays with the caller.
    """
    processes: dict[str, tuple[str, str]] = {}
    for path, pcap in paths.items():
        capture_file = f"{capture_dir}/placement_{path}.pcap"
        process_id = pcap.start_tcpdump(interfaces[path], None, output_file=capture_file)
        processes[path] = (process_id, capture_file)
    try:
        time.sleep(window_s)
    finally:
        for path, pcap in paths.items():
            process_id, _ = processes[path]
            pcap.stop_tcpdump(process_id)

    counts: dict[str, dict[str, int]] = {}
    for path, pcap in paths.items():
        _, capture_file = processes[path]
        per_stream: dict[str, int] = {}
        for index, (stream, band) in enumerate(signatures.items()):
            last = index == len(signatures) - 1
            out = pcap.tshark_read_pcap(
                capture_file,
                additional_args=f'-Y "{_band_filter(band)}" -T fields -e frame.len',
                rm_pcap=last,
            )
            per_stream[stream] = sum(1 for line in out.splitlines() if line.strip())
        counts[path] = per_stream
    return counts


def await_stream_on_path(
    paths: Mapping[str, PcapCapture],
    interfaces: Mapping[str, str],
    signature: SizeBand,
    expected_path: str,
    budget_s: float,
    anchor_monotonic: float,
    poll_s: float = 1.0,
    capture_dir: str = "/tmp",
) -> ConvergenceRecord:
    """Sample every path until *signature* lands on *expected_path* or the
    budget is spent; record the trace.

    Anchoring: *anchor_monotonic* is the ``time.monotonic()`` value the
    caller captured adjacent to the mutation whose effect is awaited — the
    elapsed figure attributes convergence to that action, so this function
    never invents its own anchor. Each poll samples **all** paths in one
    shared window (``locate_streams_by_size``); the located path is the one
    carrying the signature, ``None`` when none does. Polling continues until
    the signature is located on *expected_path* or elapsed time exceeds
    *budget_s* — the returned record carries the facts either way, and the
    budget verdict belongs to the caller.
    """
    samples: list[tuple[float, str | None]] = []
    single = {name: signature for name in ("stream",)}
    while True:
        counts = locate_streams_by_size(
            paths, interfaces, single, window_s=poll_s, capture_dir=capture_dir
        )
        elapsed = time.monotonic() - anchor_monotonic
        carrying = [path for path, per_stream in counts.items() if per_stream["stream"] > 0]
        located = max(carrying, key=lambda p: counts[p]["stream"]) if carrying else None
        samples.append((elapsed, located))
        if located == expected_path:
            return ConvergenceRecord(elapsed_s=elapsed, converged=True, samples=tuple(samples))
        if elapsed > budget_s:
            return ConvergenceRecord(elapsed_s=elapsed, converged=False, samples=tuple(samples))
