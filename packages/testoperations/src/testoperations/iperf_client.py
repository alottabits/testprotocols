"""iPerf client operations — compose iperf_client + iperf_server templates.

Receives resolved ``iperf_client`` and ``iperf_server`` template instances
from the caller.  The thin wrapper ``stop_iperf`` is deleted — step
definitions call the template method directly.
"""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass
from typing import override

from testprotocols.iperf_client import IperfClient
from testprotocols.iperf_server import IperfServer
from testprotocols.models import IperfProcess, IpFamily

from testoperations._compat import coerce_enum
from testoperations._released import ReleasedMapping
from testoperations._renamed import (
    start_receiver_session_of,
    start_sender_session_of,
    start_traffic_receiver_of,
    start_traffic_sender_of,
)


@dataclass(frozen=True, eq=False)
class IperfSession(ReleasedMapping):
    """A started iPerf session: the *sender* and *receiver* processes (each a pid and the log
    file its output goes to).

    Deprecated: reading the record like the released dict (``session["sender_pid"]``,
    :meth:`as_dict`) still works and warns; the keys are ``sender_pid``, ``sender_log``,
    ``receiver_pid`` and ``receiver_log``.
    """

    sender: IperfProcess
    receiver: IperfProcess

    @override
    def _released(self) -> dict[str, object]:
        return {
            "sender_pid": self.sender.pid,
            "sender_log": self.sender.log_file,
            "receiver_pid": self.receiver.pid,
            "receiver_log": self.receiver.log_file,
        }


def _start_receiver(server: IperfServer, port: int, family: IpFamily, udp: bool) -> IperfProcess:
    udp_only = True if udp else None
    start = start_receiver_session_of(server)
    if start is not None:
        return start(port, ip_version=family, udp_only=udp_only)
    pid, log_file = start_traffic_receiver_of(server)(port, ip_version=family, udp_only=udp_only)
    return IperfProcess(pid, log_file)


def _start_sender(
    client: IperfClient, host: str, port: int, time: int, family: IpFamily, udp: bool
) -> IperfProcess:
    start = start_sender_session_of(client)
    if start is not None:
        return start(host, port, time=time, udp_protocol=udp, ip_version=family)
    pid, log_file = start_traffic_sender_of(client)(
        host, port, time=time, udp_protocol=udp, ip_version=family
    )
    return IperfProcess(pid, log_file)


def start_iperf(
    iperf_client: IperfClient,
    iperf_server: IperfServer,
    port: int,
    time: int = 10,
    udp: bool = False,
    ip_version: IpFamily | int = IpFamily.V4,
    *,
    host: str,
) -> IperfSession:
    """Start an iPerf session: receiver first, then sender.

    The receiver listens on *port*; the sender connects to *host* on *port* for *time* seconds
    (over UDP when *udp* is true). A driver with ``start_receiver_session`` /
    ``start_sender_session`` is called by those names, one with only the released
    ``start_traffic_receiver`` / ``start_traffic_sender`` by those. *ip_version* is an
    :class:`~testprotocols.models.IpFamily`; ``4`` and ``6`` are accepted as numbers, any other
    value raises ``ValueError``. Returns the :class:`IperfSession` of both processes.

    *host* is new and keyword-only: the released operation called ``start_sender`` and
    ``start_receiver``, which no capability driver has, and had no way to name the receiver's
    address.
    """
    family = coerce_enum(IpFamily, ip_version, what="start_iperf(ip_version)")
    receiver = _start_receiver(iperf_server, port, family, udp)
    sender = _start_sender(iperf_client, host, port, time, family, udp)
    return IperfSession(sender=sender, receiver=receiver)


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
    iperf_client: IperfClient,
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

    The only :class:`~testprotocols.iperf_client.IperfClient` member used is
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
