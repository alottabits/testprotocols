"""iPerf client operations — compose iperf_client + iperf_server templates.

Receives resolved ``iperf_client`` and ``iperf_server`` template instances
from the caller.  The thin wrapper ``stop_iperf`` is deleted — step
definitions call the template method directly.
"""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass
from typing import Any


def start_iperf(
    iperf_client: Any,
    iperf_server: Any,
    port: int,
    time: int = 10,
    udp: bool = False,
    ip_version: int = 4,
) -> dict[str, Any]:
    """Start an iPerf session: receiver first, then sender.

    Returns a dict containing PIDs and log file paths for both sides:
    ``sender_pid``, ``sender_log``, ``receiver_pid``, ``receiver_log``.

    *iperf_client* and *iperf_server* are typed ``Any`` because the existing
    operation calls ``start_sender`` / ``start_receiver``, which are not part
    of the :class:`IperfClient` / :class:`IperfServer` protocol surfaces
    (``start_traffic_sender`` / ``start_traffic_receiver`` are). Pre-existing
    tech debt; logic is not modified here.
    """
    receiver_result = iperf_server.start_receiver(port, time=time, udp=udp, ip_version=ip_version)
    sender_result = iperf_client.start_sender(port, time=time, udp=udp, ip_version=ip_version)

    # Unpack (pid, log_file) tuples if the template returns them; otherwise
    # store the raw return value under _pid and _log keys.
    try:
        receiver_pid, receiver_log = receiver_result
    except (TypeError, ValueError):
        receiver_pid = receiver_result
        receiver_log = None

    try:
        sender_pid, sender_log = sender_result
    except (TypeError, ValueError):
        sender_pid = sender_result
        sender_log = None

    return {
        "sender_pid": sender_pid,
        "sender_log": sender_log,
        "receiver_pid": receiver_pid,
        "receiver_log": receiver_log,
    }


@dataclass(frozen=True)
class SenderLifeRecord:
    """A stopped sender's recorded life, parsed from its interval reports.

    ``intervals`` counts the periodic interval lines found; ``gaps`` lists
    ``(after_s, until_s)`` spans where consecutive interval end/start stamps
    do not meet (transmission holes); ``total_bytes`` sums the interval
    payloads (the end-of-run summary line, which spans the whole run, is
    excluded from all three). Facts only — whether a gap fails a run is the
    caller's judgment.
    """

    intervals: int
    gaps: tuple[tuple[float, float], ...]
    total_bytes: int


_INTERVAL_RE = re.compile(
    r"\[\s*\d+\]\s+(?P<start>\d+(?:\.\d+)?)\s*-\s*(?P<end>\d+(?:\.\d+)?)\s+sec"
    r"\s+(?P<size>\d+(?:\.\d+)?)\s+(?P<unit>[KMG]?)Bytes"
)

_UNIT_BYTES = {"": 1, "K": 1024, "M": 1024**2, "G": 1024**3}


def sender_life_record(
    iperf_client: Any,
    log_file: str,
    gap_tolerance_s: float = 0.5,
) -> SenderLifeRecord:
    """Parse the sender log at *log_file* into a :class:`SenderLifeRecord`.

    Requires the sender to have run with periodic interval reporting (both
    iperf generations print ``[ id]  a.b- c.d sec   N xBytes …`` interval
    lines); a log without interval lines parses to ``intervals=0``, which a
    caller should treat as "no recorded life", not as continuity. The
    end-of-run summary is recognized as the row spanning from the first
    interval's start to the last stamp and is excluded. A hole between one
    interval's end and the next interval's start larger than
    *gap_tolerance_s* is recorded as a gap.

    *iperf_client* is typed ``Any`` for consistency with this module's
    existing operations; the only member used is the
    :class:`~testprotocols.iperf_client.IperfClient` surface's
    ``get_iperf_logs``.
    """
    log = iperf_client.get_iperf_logs(log_file)
    rows: list[tuple[float, float, int]] = []
    for match in _INTERVAL_RE.finditer(log):
        start = float(match.group("start"))
        end = float(match.group("end"))
        size = float(match.group("size")) * _UNIT_BYTES[match.group("unit")]
        rows.append((start, end, int(size)))

    if not rows:
        return SenderLifeRecord(intervals=0, gaps=(), total_bytes=0)

    rows.sort(key=lambda r: (r[0], r[1]))
    last_end = max(end for _, end, _ in rows)
    first_start = rows[0][0]
    # The end-of-run summary repeats the whole span (first start -> last
    # stamp); periodic intervals never do unless the run had exactly one.
    periodic = [r for r in rows if not (r[0] == first_start and r[1] == last_end)] or rows

    gaps: list[tuple[float, float]] = []
    for (_, prev_end, _), (next_start, _, _) in itertools.pairwise(periodic):
        if next_start - prev_end > gap_tolerance_s:
            gaps.append((prev_end, next_start))

    return SenderLifeRecord(
        intervals=len(periodic),
        gaps=tuple(gaps),
        total_bytes=sum(size for _, _, size in periodic),
    )
