"""Concurrent iperf3 throughput measurement over typed iperf capabilities.

Framing owned here (the reason this is a ``testoperations`` function and not a
step one-liner): start every receiver FIRST (one iperf3 server instance per
flow, each on its own port), snapshot each receiver log's completed-session
count, launch all senders together so the flows genuinely overlap, then poll
each receiver log until a NEW completed session appears and report its
measured rate. The RECEIVE side is read deliberately: the receiver sits behind
the device under test, so its rate is what actually crossed that device
(send-side rates include bytes a shaper may still be queueing or dropping).

Assertion-free and stdlib-only: returns facts (per-flow Mbit/s) and raises only
on operational failures (duplicate ports, a receiver that never produces a
completed session). Pass/fail thresholds belong to the caller.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from testprotocols.iperf_client import IperfClient
from testprotocols.iperf_server import IperfServer

# A finished iperf3 session is flushed to the --logfile when the sender
# disconnects; allow a grace window after the nominal duration for that flush
# (and for clock skew between controller and endpoints).
DEFAULT_RESULT_TIMEOUT_S = 30.0
_POLL_INTERVAL_S = 1.0


@dataclass(frozen=True)
class ThroughputFlow:
    """One measured flow: *sender* connects to *dest_host*:*port*, *receiver* listens.

    ``port`` must be unique across the flows of one measurement call — each
    flow gets its own iperf3 server instance (and per-port logfile) on the
    receiving device.

    ``reverse`` runs the session in iperf3 reverse mode (``-R``): the *sender*
    still initiates the connection, but the listening *receiver* transmits the
    data (a download, from the initiating side's point of view). The reported
    rate stays receive-side goodput either way — iperf3 exchanges end-of-test
    summaries, so ``end.sum_received`` in the receiver's log is what the
    data-receiving side actually got in both directions.

    ``omit_s`` skips the first N seconds of the session (iperf3 ``-O``: the
    TCP slow-start ramp) — omitted seconds extend the wall-clock run and are
    excluded from the reported summary, so the rate is steady-state by
    construction.
    """

    sender: IperfClient
    receiver: IperfServer
    dest_host: str
    port: int
    reverse: bool = False
    omit_s: int = 0


@dataclass(frozen=True)
class FlowThroughput:
    """The measured receive-side rate (and sending-socket RTT) of one flow.

    ``min_rtt_ms`` / ``mean_rtt_ms`` are the loaded connection's TCP round-trip
    time as sampled by the kernel of the data-sending side (iperf3 stamps
    ``TCP_INFO`` into ``end.streams[*].sender``), in milliseconds. ``None``
    when the session carried no RTT samples (UDP, or an iperf3 build that does
    not exchange them).
    """

    port: int
    mbps: float
    min_rtt_ms: float | None = None
    mean_rtt_ms: float | None = None


def iter_json_docs(text: str) -> list[Any]:
    """Parse the top-level JSON documents concatenated in *text*, in order.

    iperf3 appends one pretty-printed JSON document per session to its
    ``--logfile``; a restarted server appends to the same per-port file, so a
    log may hold several documents (and a trailing, still-open one while a
    session is running). Documents are extracted with a string-aware brace
    scanner; only complete, parseable documents are returned.
    """
    docs: list[Any] = []
    depth = 0
    start = -1
    in_string = False
    escaped = False
    for i, ch in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    docs.append(json.loads(text[start : i + 1]))
                except ValueError:
                    pass
                start = -1
    return docs


def count_sessions(log_text: str) -> int:
    """The number of completed iperf3 session documents in *log_text*."""
    return len(iter_json_docs(log_text))


def _direction_fragment(flow: ThroughputFlow) -> str | None:
    """The iperf3 CLI fragment realizing *flow*'s reverse/omit options.

    The ``IperfClient.start_traffic_sender`` ``direction`` parameter is a raw
    command-line fragment appended verbatim by the implementations; reverse
    mode and the slow-start omit ride on it, so no protocol change is needed.
    """
    parts: list[str] = []
    if flow.reverse:
        parts.append("-R")
    if flow.omit_s:
        parts.append(f"-O {flow.omit_s}")
    # The sender's own log must be JSON: a forward flow's RTT lives ONLY in
    # the data-sending (client) side's output — live-diagnosed 2026-07-06,
    # the server-side log carries no sender RTT for client-sent sessions.
    parts.append("--json")
    return " ".join(parts)


def last_session_rtt_ms(log_text: str) -> tuple[float | None, float | None]:
    """``(min_rtt_ms, mean_rtt_ms)`` of the LAST completed session's sending side.

    iperf3 stamps the data-sending socket's ``TCP_INFO`` round-trip stats into
    ``end.streams[*].sender`` (``min_rtt`` / ``mean_rtt``, in microseconds) and
    both sides exchange end-of-test summaries, so the receiver's ``--json``
    log carries them for either direction. Multi-stream sessions aggregate as
    the minimum of the minima and the mean of the means. The pair is
    both-or-neither: ``(None, None)`` when no completed session carries a
    complete set of RTT samples (UDP, an iperf3 build that does not exchange
    ``TCP_INFO``, or a document with only one of the two fields) — callers
    never see a half-populated pair.
    """
    docs = iter_json_docs(log_text)
    if not docs or not isinstance(docs[-1], dict):
        return (None, None)
    streams = docs[-1].get("end", {}).get("streams", [])
    mins: list[float] = []
    means: list[float] = []
    for stream in streams:
        sender = stream.get("sender", {}) if isinstance(stream, dict) else {}
        if not isinstance(sender, dict):
            continue
        if sender.get("min_rtt") is not None:
            mins.append(float(sender["min_rtt"]))
        if sender.get("mean_rtt") is not None:
            means.append(float(sender["mean_rtt"]))
    if not mins or not means:
        return (None, None)
    return (min(mins) / 1000.0, (sum(means) / len(means)) / 1000.0)


def last_session_mbps(log_text: str) -> float | None:
    """The receive-side rate (Mbit/s) of the LAST completed session, or ``None``.

    Prefers ``end.sum_received.bits_per_second`` (TCP receive-side goodput);
    falls back to ``end.sum.bits_per_second`` (UDP sessions). Returns ``None``
    when no completed session carries either summary.
    """
    docs = iter_json_docs(log_text)
    if not docs:
        return None
    end = docs[-1].get("end", {}) if isinstance(docs[-1], dict) else {}
    for key in ("sum_received", "sum"):
        bps = end.get(key, {}).get("bits_per_second")
        if bps is not None:
            return float(bps) / 1e6
    return None


def _sending_side_rtt(
    flow: ThroughputFlow,
    *,
    receiver_text: str,
    sender_log: str,
    deadline: float,
    sleep: Callable[[float], None],
    monotonic: Callable[[], float],
) -> tuple[float | None, float | None]:
    """RTT of *flow*'s data-sending side, read from that side's own logfile.

    Reverse flow: the listening receiver transmits — its already-fetched
    session text is the sending side. Forward flow: the client transmits —
    poll its ``--json`` log (the launch shell-redirect truncates it, so the
    first completed document IS this session) until a session appears or
    *deadline* passes. No session by the deadline -> ``(None, None)``: the
    rate was already confirmed receive-side, so RTT degrades rather than
    failing the measurement.
    """
    if flow.reverse:
        return last_session_rtt_ms(receiver_text)
    while True:
        text = flow.sender.get_iperf_logs(sender_log)
        if count_sessions(text) > 0:
            return last_session_rtt_ms(text)
        if monotonic() >= deadline:
            return (None, None)
        sleep(_POLL_INTERVAL_S)


def measure_concurrent_throughput(
    flows: Sequence[ThroughputFlow],
    *,
    duration_s: int = 10,
    result_timeout_s: float = DEFAULT_RESULT_TIMEOUT_S,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> list[FlowThroughput]:
    """Run all *flows* concurrently for *duration_s*; return per-flow receive rates.

    Receivers are started before any sender (no connection race), every sender
    is launched before the measurement wait (the flows overlap for the whole
    duration), and both sides are stopped in a ``finally`` so no iperf process
    outlives the call — also on failure. Results are ordered like *flows*.

    Raises ``ValueError`` on duplicate ports (two flows would share a server
    instance and logfile) and ``RuntimeError`` when a receiver produces no new
    completed session within *duration_s* + *result_timeout_s*.

    RTT is read from the **data-sending side's own logfile** — the only place
    the sending socket's ``TCP_INFO`` reliably appears (live-diagnosed
    2026-07-06: the server-side log carries no sender RTT for client-sent
    sessions). Forward flow -> the sender's ``--json`` log; reverse flow ->
    the receiver's log (the listener transmits there). A sending-side log
    that yields no completed session before the deadline degrades to RTT
    ``(None, None)`` — the rate, already confirmed receive-side, is returned
    either way.
    """
    ports = [f.port for f in flows]
    if len(set(ports)) != len(ports):
        raise ValueError(f"flow ports must be unique per measurement, got {ports}")

    started: list[tuple[ThroughputFlow, int, str, int]] = []
    senders: list[tuple[IperfClient, int, str]] = []  # (sender, pid, log) per flow
    try:
        for flow in flows:
            receiver_pid, receiver_log = flow.receiver.start_traffic_receiver(flow.port)
            prior_sessions = count_sessions(flow.receiver.get_iperf_logs(receiver_log))
            started.append((flow, receiver_pid, receiver_log, prior_sessions))

        for flow, _, _, _ in started:
            sender_pid, sender_log = flow.sender.start_traffic_sender(
                flow.dest_host,
                flow.port,
                time=duration_s,
                direction=_direction_fragment(flow),
            )
            senders.append((flow.sender, sender_pid, sender_log))

        # Omitted slow-start seconds extend the wall clock beyond duration_s.
        sleep(float(duration_s + max((f.omit_s for f in flows), default=0)))

        results: list[FlowThroughput] = []
        deadline = monotonic() + result_timeout_s
        for (flow, _, receiver_log, prior_sessions), (_, _, sender_log) in zip(
            started, senders, strict=True
        ):
            while True:
                log_text = flow.receiver.get_iperf_logs(receiver_log)
                if count_sessions(log_text) > prior_sessions:
                    mbps = last_session_mbps(log_text)
                    if mbps is not None:
                        min_rtt_ms, mean_rtt_ms = _sending_side_rtt(
                            flow,
                            receiver_text=log_text,
                            sender_log=sender_log,
                            deadline=deadline,
                            sleep=sleep,
                            monotonic=monotonic,
                        )
                        results.append(
                            FlowThroughput(
                                port=flow.port,
                                mbps=mbps,
                                min_rtt_ms=min_rtt_ms,
                                mean_rtt_ms=mean_rtt_ms,
                            )
                        )
                        break
                if monotonic() >= deadline:
                    raise RuntimeError(
                        f"iperf receiver on port {flow.port} produced no completed "
                        f"session within {result_timeout_s}s after the "
                        f"{duration_s}s measurement window"
                    )
                sleep(_POLL_INTERVAL_S)
        return results
    finally:
        for sender, sender_pid, _ in senders:
            try:
                sender.stop_traffic(sender_pid)
            except Exception:
                pass
        for flow, receiver_pid, _, _ in started:
            try:
                flow.receiver.stop_traffic(receiver_pid)
            except Exception:
                pass
