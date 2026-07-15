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

    ``bandwidth_mbps`` caps the sender's offered rate (iperf3 ``-b Nm``). A
    low value turns the flow into a **non-saturating path-RTT probe**: it
    never fills the bottleneck queue, so its ``min_rtt_ms``/``mean_rtt_ms``
    read the path's idle round-trip time instead of the standing queue a
    saturating flow builds.

    ``window`` pins the socket buffer on both ends (iperf3 ``-w``, e.g.
    ``"8M"``), disabling OS autotuning — the standard measurement-rig remedy
    for receive-window autotuning stalls on high-BDP paths. ``None`` keeps
    autotuning. The effective value is capped by ``net.core.rmem_max`` /
    ``wmem_max`` on the endpoint hosts.
    """

    sender: IperfClient
    receiver: IperfServer
    dest_host: str
    port: int
    reverse: bool = False
    omit_s: int = 0
    bandwidth_mbps: int | None = None
    window: str | None = None


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


def _await_session(
    read_log: Callable[[str], str],
    log_path: str,
    prior_sessions: int,
    deadline: float,
    sleep: Callable[[float], None],
    monotonic: Callable[[], float],
) -> tuple[str, float] | None:
    """Poll *log_path* for a NEW completed session carrying a rate summary.

    Returns ``(log_text, last_session_mbps)`` once more than *prior_sessions*
    completed documents are present and the last one has a rate summary;
    ``None`` when *deadline* passes first.
    """
    while True:
        text = read_log(log_path)
        if count_sessions(text) > prior_sessions:
            mbps = last_session_mbps(text)
            if mbps is not None:
                return (text, mbps)
        if monotonic() >= deadline:
            return None
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

    Each quantity is read from the side that actually observed it — iperf3's
    end-of-test exchange copies NEITHER across sides on real builds
    (live-diagnosed 2026-07-06: the server-side log has no sender RTT for
    client-sent sessions, and near-zero ``sum_received`` for reverse
    sessions where the server transmitted):

    - **rate** comes from the data-RECEIVING side's own log — the listening
      receiver for a forward flow, the initiating sender device for a
      reverse flow (its ``--json`` log; the launch shell-redirect truncates
      the file, so the first completed document is this session);
    - **RTT** comes from the data-SENDING side's own log (its socket's
      ``TCP_INFO``) — the sender's log for a forward flow, the receiver's
      log for a reverse flow.

    A forward flow whose sender log yields no session by the deadline
    degrades to RTT ``(None, None)`` (the rate was already confirmed); a
    reverse flow in that state raises ``RuntimeError`` — its rate lives in
    that log, so there is no result to report.
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
                bandwidth=flow.bandwidth_mbps,
                time=duration_s,
                reverse=flow.reverse,
                omit_s=flow.omit_s or None,
                # The sender's own log must be JSON: a forward flow's RTT
                # lives ONLY in the data-sending (client) side's output —
                # live-diagnosed 2026-07-06.
                json_output=True,
                window=flow.window,
            )
            senders.append((flow.sender, sender_pid, sender_log))

        # Omitted slow-start seconds extend the wall clock beyond duration_s.
        sleep(float(duration_s + max((f.omit_s for f in flows), default=0)))

        results: list[FlowThroughput] = []
        deadline = monotonic() + result_timeout_s
        for (flow, _, receiver_log, prior_sessions), (_, _, sender_log) in zip(
            started, senders, strict=True
        ):
            rx = _await_session(
                flow.receiver.get_iperf_logs,
                receiver_log,
                prior_sessions,
                deadline,
                sleep,
                monotonic,
            )
            if rx is None:
                raise RuntimeError(
                    f"iperf receiver on port {flow.port} produced no completed "
                    f"session within {result_timeout_s}s after the "
                    f"{duration_s}s measurement window"
                )
            receiver_text, rx_mbps = rx
            tx = _await_session(
                flow.sender.get_iperf_logs, sender_log, 0, deadline, sleep, monotonic
            )
            if flow.reverse:
                if tx is None:
                    raise RuntimeError(
                        f"reverse flow on port {flow.port}: the initiating "
                        f"(data-receiving) side produced no completed session "
                        f"within {result_timeout_s}s — no receive-side rate"
                    )
                _, mbps = tx
                min_rtt_ms, mean_rtt_ms = last_session_rtt_ms(receiver_text)
            else:
                mbps = rx_mbps
                min_rtt_ms, mean_rtt_ms = (
                    last_session_rtt_ms(tx[0]) if tx is not None else (None, None)
                )
            results.append(
                FlowThroughput(
                    port=flow.port,
                    mbps=mbps,
                    min_rtt_ms=min_rtt_ms,
                    mean_rtt_ms=mean_rtt_ms,
                )
            )
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


# --- rated-path measurement: unloaded RTT probe + sequential directions -------
#
# The framing owned here (the reason it is a testoperations function and not a
# step loop): a rated-performance check of a forwarding path is one unloaded
# path-RTT probe plus each direction measured on its own — the directions run
# SEQUENTIALLY, not concurrently, because each must own the path to reach its
# rated figure (unlike measure_concurrent_throughput's overlapping flows). A
# freshly-written policy converges eventually, so the round repeats until the
# caller's stop predicate is satisfied or a time budget lapses. This is a
# MECHANIC, not a policy: it reports every round's findings and never decides
# whether they are acceptable — per-round thresholds, what "settled" means
# (e.g. reproducibility across N rounds), and any pass/fail verdict all live
# with the caller. Aside from operational failures it raises nothing.

DEFAULT_PROBE_RATE_MBPS = 1
DEFAULT_PROBE_DURATION_S = 3
DEFAULT_MEASURE_DURATION_S = 10


@dataclass(frozen=True)
class DirectionSpec:
    """One measurement round: a *name* label and its iperf3 direction.

    ``reverse`` runs the round in iperf3 reverse mode (the listening receiver
    transmits — a download from the initiating side). The caller owns the
    name↔direction convention (e.g. ``upload``→forward, ``download``→reverse);
    this operation only carries it through to the flow.
    """

    name: str
    reverse: bool


@dataclass(frozen=True)
class PathMeasurement:
    """Facts from one probe+directions round (assertion-free).

    ``probe_min_rtt_ms`` / ``probe_mean_rtt_ms`` are the path's UNLOADED RTT
    from the rate-capped probe (``(None, None)`` if the probe carried no RTT
    samples). ``by_direction`` maps each :class:`DirectionSpec` name to its
    measured :class:`FlowThroughput` (loaded rate + loaded-RTT evidence).
    """

    probe_min_rtt_ms: float | None
    probe_mean_rtt_ms: float | None
    by_direction: dict[str, FlowThroughput]


def measure_path_rtt(
    sender: IperfClient,
    receiver: IperfServer,
    dest_host: str,
    port: int,
    *,
    rate_mbps: int = DEFAULT_PROBE_RATE_MBPS,
    duration_s: int = DEFAULT_PROBE_DURATION_S,
    measure: Callable[..., list[FlowThroughput]] = measure_concurrent_throughput,
) -> tuple[float | None, float | None]:
    """The path's unloaded ``(min, mean)`` RTT via one rate-capped probe flow.

    The flow is capped far below the path's capacity (``rate_mbps``) so it never
    builds a bottleneck queue — its RTT reads the idle path, not the standing
    queue a saturating flow keeps. Returns the probe's ``(min_rtt_ms,
    mean_rtt_ms)`` pair (both-or-neither, per :func:`last_session_rtt_ms`).
    """
    flow = ThroughputFlow(
        sender=sender,
        receiver=receiver,
        dest_host=dest_host,
        port=port,
        bandwidth_mbps=rate_mbps,
    )
    (result,) = measure([flow], duration_s=duration_s)
    return result.min_rtt_ms, result.mean_rtt_ms


def measure_one_direction(
    sender: IperfClient,
    receiver: IperfServer,
    dest_host: str,
    port: int,
    *,
    reverse: bool,
    duration_s: int = DEFAULT_MEASURE_DURATION_S,
    omit_s: int = 0,
    window: str | None = None,
    measure: Callable[..., list[FlowThroughput]] = measure_concurrent_throughput,
) -> FlowThroughput:
    """Measure a single saturating flow in one direction (forward or reverse).

    ``reverse=False`` sends *sender*→*receiver* (an upload from the sender's
    side); ``reverse=True`` runs iperf3 reverse mode so the receiver transmits
    (a download). The reported rate is receive-side goodput either way.

    ``window`` pins the flow's socket buffers (see :class:`ThroughputFlow`).
    """
    flow = ThroughputFlow(
        sender=sender,
        receiver=receiver,
        dest_host=dest_host,
        port=port,
        reverse=reverse,
        omit_s=omit_s,
        window=window,
    )
    (result,) = measure([flow], duration_s=duration_s)
    return result


# --- external-endpoint measurement (client-log-only) --------------------------
#
# A public iperf3 endpoint is reachable but not DRIVEN: there is no
# ``IperfServer`` capability behind it, no way to start/stop its listener, and
# no server-side log to read. Every fact must come from the initiating
# client's own ``--json`` log. That is sufficient for the rate in BOTH
# directions: for a forward flow iperf3's end-of-test exchange places the
# remote side's receive summary in the client log's ``end.sum_received``, and
# for a reverse flow the client IS the data receiver, so ``end.sum_received``
# is its own goodput. RTT is observable only when the client is the
# data-SENDING side (its socket's ``TCP_INFO``): forward flows carry it;
# reverse flows report ``(None, None)`` — callers judge latency on a forward
# (probe) flow, exactly as :func:`measure_path_until` callers already do.
#
# A public endpoint can also REFUSE a session (typically "the server is busy
# running a test"): iperf3 then writes an ``error`` document to the log.
# That is surfaced as a ``RuntimeError`` naming the endpoint's reason —
# an operational failure distinct from "no result within the timeout".


@dataclass(frozen=True)
class ExternalFlow:
    """One client-driven flow toward an endpoint that is not testbed-managed.

    Field semantics match :class:`ThroughputFlow` where they overlap;
    ``parallel`` runs the session over N parallel streams (iperf3 ``-P``),
    whose end-of-test summaries aggregate into ONE reported rate.
    """

    sender: IperfClient
    dest_host: str
    port: int
    reverse: bool = False
    parallel: int | None = None
    omit_s: int = 0
    bandwidth_mbps: int | None = None
    window: str | None = None


class EndpointBusyError(RuntimeError):
    """A public endpoint refused the session because it is serving another test.

    iperf3 surfaces this as an ``error`` document ("the server is busy
    running a test. try again later"). On a shared public pool this is a
    NORMAL transient condition, distinct from a real operational failure —
    :func:`measure_external_path_until` retries it on the next pool port
    within its budget; other endpoint errors propagate immediately.
    """


def last_session_error(log_text: str) -> str | None:
    """The ``error`` string of the LAST completed session document, or ``None``."""
    docs = iter_json_docs(log_text)
    if not docs or not isinstance(docs[-1], dict):
        return None
    error = docs[-1].get("error")
    return str(error) if error else None


def _await_client_session(
    read_log: Callable[[str], str],
    log_path: str,
    deadline: float,
    sleep: Callable[[float], None],
    monotonic: Callable[[], float],
) -> tuple[str, float]:
    """Poll the CLIENT log for a completed session; raise on endpoint errors.

    The client launch truncates its own log (shell redirect), so the first
    completed document is this session. An ``error`` document (endpoint
    refused/aborted the session) raises immediately with the endpoint's
    reason; a log that never completes raises when *deadline* passes.
    """
    while True:
        text = read_log(log_path)
        error = last_session_error(text)
        if error is not None:
            if "busy" in error:
                raise EndpointBusyError(f"iperf3 endpoint session failed: {error}")
            raise RuntimeError(f"iperf3 endpoint session failed: {error}")
        if count_sessions(text) > 0:
            mbps = last_session_mbps(text)
            if mbps is not None:
                return (text, mbps)
        if monotonic() >= deadline:
            raise RuntimeError(
                f"external iperf session toward {log_path!r} produced no "
                f"completed client-side result before the timeout"
            )
        sleep(_POLL_INTERVAL_S)


def measure_external_flow(
    flow: ExternalFlow,
    *,
    duration_s: int = DEFAULT_MEASURE_DURATION_S,
    result_timeout_s: float = DEFAULT_RESULT_TIMEOUT_S,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> FlowThroughput:
    """Run one client-driven flow against an unmanaged endpoint; report its facts.

    The sender is stopped in a ``finally`` so no iperf process outlives the
    call — also on failure. The reported rate is ``end.sum_received`` from the
    client's own log (receive-side goodput in both directions — see the
    section comment); RTT is client-side ``TCP_INFO`` for a forward flow and
    ``(None, None)`` for a reverse flow (the data sender is the remote
    endpoint, whose kernel we cannot read).
    """
    sender_pid, sender_log = flow.sender.start_traffic_sender(
        flow.dest_host,
        flow.port,
        bandwidth=flow.bandwidth_mbps,
        time=duration_s,
        reverse=flow.reverse,
        omit_s=flow.omit_s or None,
        json_output=True,
        window=flow.window,
        parallel=flow.parallel,
    )
    try:
        sleep(float(duration_s + flow.omit_s))
        text, mbps = _await_client_session(
            flow.sender.get_iperf_logs,
            sender_log,
            monotonic() + result_timeout_s,
            sleep,
            monotonic,
        )
    finally:
        try:
            flow.sender.stop_traffic(sender_pid)
        except Exception:
            pass
    if flow.reverse:
        min_rtt_ms: float | None = None
        mean_rtt_ms: float | None = None
    else:
        min_rtt_ms, mean_rtt_ms = last_session_rtt_ms(text)
    return FlowThroughput(port=flow.port, mbps=mbps, min_rtt_ms=min_rtt_ms, mean_rtt_ms=mean_rtt_ms)


def measure_external_path_until(
    *,
    sender: IperfClient,
    dest_host: str,
    directions: Sequence[DirectionSpec],
    allocate_port: Callable[[], int],
    stop_when: Callable[[list[PathMeasurement]], bool],
    budget_s: float,
    parallel: int | None = None,
    probe_rate_mbps: int = DEFAULT_PROBE_RATE_MBPS,
    probe_duration_s: int = DEFAULT_PROBE_DURATION_S,
    measure_duration_s: int = DEFAULT_MEASURE_DURATION_S,
    omit_s: int = 0,
    window: str | None = None,
    on_round: Callable[[PathMeasurement], None] | None = None,
    measure_flow: Callable[..., FlowThroughput] = measure_external_flow,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    busy_backoff_s: float = 5.0,
) -> list[PathMeasurement]:
    """The :func:`measure_path_until` loop against an unmanaged endpoint.

    Identical framing and caller contract — one unloaded forward RTT probe,
    then each direction measured sequentially, rounds repeating until
    *stop_when* or *budget_s* — with every flow client-driven
    (:func:`measure_external_flow`). ``parallel`` applies to the saturating
    direction flows only; the probe is always a single rate-capped stream
    (it must not saturate, and its forward direction is what makes the
    client-side RTT observable). ``window`` likewise applies to the
    direction flows only.

    A **busy** endpoint (:class:`EndpointBusyError` — the shared public
    pool serving someone else) is retried on the NEXT allocated pool port
    after ``busy_backoff_s``, within the same budget; any other endpoint
    error propagates immediately.
    """
    deadline = monotonic() + budget_s

    def _flow_with_busy_retry(
        build: Callable[[int], ExternalFlow], duration_s: int
    ) -> FlowThroughput:
        while True:
            try:
                return measure_flow(build(allocate_port()), duration_s=duration_s)
            except EndpointBusyError:
                if monotonic() >= deadline:
                    raise
                sleep(busy_backoff_s)

    findings: list[PathMeasurement] = []
    while True:
        probe = _flow_with_busy_retry(
            lambda port: ExternalFlow(
                sender=sender,
                dest_host=dest_host,
                port=port,
                bandwidth_mbps=probe_rate_mbps,
            ),
            probe_duration_s,
        )
        by_direction: dict[str, FlowThroughput] = {}
        for spec in directions:

            def _direction_flow(port: int, spec: DirectionSpec = spec) -> ExternalFlow:
                return ExternalFlow(
                    sender=sender,
                    dest_host=dest_host,
                    port=port,
                    reverse=spec.reverse,
                    parallel=parallel,
                    omit_s=omit_s,
                    window=window,
                )

            by_direction[spec.name] = _flow_with_busy_retry(_direction_flow, measure_duration_s)
        facts = PathMeasurement(
            probe_min_rtt_ms=probe.min_rtt_ms,
            probe_mean_rtt_ms=probe.mean_rtt_ms,
            by_direction=by_direction,
        )
        findings.append(facts)
        if on_round is not None:
            on_round(facts)
        if stop_when(findings) or monotonic() >= deadline:
            return findings


def measure_path_until(
    *,
    sender: IperfClient,
    receiver: IperfServer,
    dest_host: str,
    directions: Sequence[DirectionSpec],
    allocate_port: Callable[[], int],
    stop_when: Callable[[list[PathMeasurement]], bool],
    budget_s: float,
    probe_rate_mbps: int = DEFAULT_PROBE_RATE_MBPS,
    probe_duration_s: int = DEFAULT_PROBE_DURATION_S,
    measure_duration_s: int = DEFAULT_MEASURE_DURATION_S,
    omit_s: int = 0,
    window: str | None = None,
    on_round: Callable[[PathMeasurement], None] | None = None,
    measure: Callable[..., list[FlowThroughput]] = measure_concurrent_throughput,
    monotonic: Callable[[], float] = time.monotonic,
) -> list[PathMeasurement]:
    """Measure probe+directions rounds until *stop_when* or *budget_s*; report all.

    One round is: a single unloaded RTT probe, then each *directions* entry
    measured sequentially (each owns the path). ``allocate_port`` hands out a
    fresh, collision-free port for every flow (probe and each direction, every
    round). ``on_round`` — if given — is called with each round's facts as they
    are produced (a logging seam).

    After each round, *stop_when* receives the findings so far (the ordered list
    of every round's :class:`PathMeasurement`) and returns ``True`` to stop. This
    is where the CALLER's acceptability policy lives — per-round thresholds, what
    "settled" means (e.g. N consecutive passing rounds), when to give up. The
    loop also stops when ``budget_s`` lapses. ``stop_when`` MAY raise to signal a
    terminal, non-retryable condition; that exception propagates without a retry.

    ``window`` applies to the saturating direction flows only; the unloaded
    RTT probe never pins buffers (it must not saturate, so autotuning is
    irrelevant and the probe stays representative of the idle path).

    Returns every round's findings in order — never a verdict. Whether those
    findings are acceptable (settled, marginal, or a failure) is entirely the
    caller's decision. Operational failures from the underlying measurement
    (duplicate ports, a receiver that never completes) propagate as they do from
    :func:`measure_concurrent_throughput`.
    """
    deadline = monotonic() + budget_s
    findings: list[PathMeasurement] = []
    while True:
        probe_min, probe_mean = measure_path_rtt(
            sender,
            receiver,
            dest_host,
            allocate_port(),
            rate_mbps=probe_rate_mbps,
            duration_s=probe_duration_s,
            measure=measure,
        )
        by_direction: dict[str, FlowThroughput] = {}
        for spec in directions:
            by_direction[spec.name] = measure_one_direction(
                sender,
                receiver,
                dest_host,
                allocate_port(),
                reverse=spec.reverse,
                duration_s=measure_duration_s,
                omit_s=omit_s,
                window=window,
                measure=measure,
            )
        facts = PathMeasurement(
            probe_min_rtt_ms=probe_min,
            probe_mean_rtt_ms=probe_mean,
            by_direction=by_direction,
        )
        findings.append(facts)
        if on_round is not None:
            on_round(facts)
        if stop_when(findings) or monotonic() >= deadline:
            return findings
