"""Poll-until-converge waiting operations.

Distributed-system state (route propagation, policy pushes, log delivery) is
eventual, so tests observe it by polling a boolean signal until it reads the
wanted way or a time budget lapses. These are MECHANICS, not policies: the
budget, the interval, and what to do about a ``False`` verdict all live with
the caller — nothing here raises on expiry or decides pass/fail.

``probe_reachable`` / ``wait_for_reachability`` bind the skeleton to the
:class:`~testprotocols.network_probe.NetworkProbe` contract for the common
L3/L4 case; ``await_reachability`` is their result-returning sibling for
callers that record evidence of the convergence (the probe's last reading
plus the poll loop, never the bare match verdict). UDP verdicts are only
meaningful when the target runs a responder (see the protocol's docstring) —
ensuring one is the caller's arrangement.

The module imports only testprotocols contracts — no devices, no vendor SDKs.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from testprotocols.network_probe import NetworkProbe

# iperf3's default port, the convention the tcp/udp probes' responders follow.
DEFAULT_TCP_PORT = 5201
DEFAULT_UDP_PORT = 5201


def wait_until(
    predicate: Callable[[], bool],
    *,
    budget_s: float,
    interval_s: float,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> bool:
    """Poll *predicate* until it returns ``True`` or *budget_s* lapses.

    Returns whether the ``True`` verdict was observed within the budget —
    never a verdict on what that means. *predicate* is always evaluated at
    least once, including with a zero or negative budget. Exceptions from
    *predicate* propagate (a terminal condition, not a retry).
    """
    deadline = monotonic() + budget_s
    while True:
        if predicate():
            return True
        if monotonic() >= deadline:
            return False
        sleep(interval_s)


def probe_reachable(
    probe: NetworkProbe,
    proto: str,
    target_ip: str,
    *,
    tcp_port: int = DEFAULT_TCP_PORT,
    udp_port: int = DEFAULT_UDP_PORT,
) -> bool:
    """Run one reachability probe toward *target_ip* over *proto* (icmp/tcp/udp)."""
    if proto == "icmp":
        return bool(probe.icmp_can_reach(target_ip))
    if proto == "tcp":
        return bool(probe.tcp_can_connect(target_ip, tcp_port))
    if proto == "udp":
        return bool(probe.udp_can_reach(target_ip, udp_port))
    raise ValueError(f"unsupported probe protocol {proto!r} (expected icmp/tcp/udp)")


def wait_for_reachability(
    probe: NetworkProbe,
    proto: str,
    target_ip: str,
    *,
    want: bool,
    budget_s: float,
    interval_s: float,
    tcp_port: int = DEFAULT_TCP_PORT,
    udp_port: int = DEFAULT_UDP_PORT,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> bool:
    """Poll until the probe verdict equals *want*, or the budget expires.

    Returns ``True`` if the wanted verdict was observed within the budget.
    Used both ways: ``want=True`` waits for connectivity to converge,
    ``want=False`` waits for a deny to take effect.

    A readiness gate for callers that record nothing about the wait. A
    caller recording evidence of the convergence composes
    :func:`await_reachability` instead — this bool answers whether the poll
    matched *want*, not what the probe read.
    """
    return wait_until(
        lambda: (
            probe_reachable(probe, proto, target_ip, tcp_port=tcp_port, udp_port=udp_port) is want
        ),
        budget_s=budget_s,
        interval_s=interval_s,
        sleep=sleep,
        monotonic=monotonic,
    )


@dataclass(frozen=True)
class ReachabilityAwait:
    """The probe's last reading plus the poll loop that found it."""

    reachable: bool
    elapsed_s: float
    polls: int
    poll_interval_s: float
    not_converged_at_s: float | None


def _await_reading(
    read: Callable[[], bool],
    *,
    want: bool,
    budget_s: float,
    interval_s: float,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> ReachabilityAwait:
    """Drive *read* through ``wait_until`` and keep its LAST reading.

    The shared reading-loop core: public awaits bind a concrete probe to
    *read* and stay intent-named, so a new probe surface joins as its own
    sibling rather than widening one generalized signature.
    """
    last = [not want]
    rounds = 0
    still_wrong_at: float | None = None
    start = monotonic()

    def _matches() -> bool:
        nonlocal rounds, still_wrong_at
        rounds += 1
        last[0] = read()
        if last[0] is want:
            return True
        # This round still read the old state: the lower bound on when the
        # system could have converged.
        still_wrong_at = monotonic() - start
        return False

    wait_until(_matches, budget_s=budget_s, interval_s=interval_s, sleep=sleep, monotonic=monotonic)
    return ReachabilityAwait(
        reachable=last[0],
        elapsed_s=monotonic() - start,
        polls=rounds,
        poll_interval_s=interval_s,
        not_converged_at_s=still_wrong_at,
    )


def await_reachability(
    probe: NetworkProbe,
    proto: str,
    target_ip: str,
    *,
    want: bool,
    budget_s: float,
    interval_s: float,
    tcp_port: int = DEFAULT_TCP_PORT,
    udp_port: int = DEFAULT_UDP_PORT,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> ReachabilityAwait:
    """Poll until the probe reads *want*; return the probe's LAST reading.

    The result-returning sibling of :func:`wait_for_reachability`: use the
    bool wait as a readiness gate that records nothing; compose this await
    wherever the caller records evidence of the convergence, because such a
    record needs what the probe actually READ, never whether the poll
    matched *want* — on budget expiry against a flow that never converged,
    ``reachable`` is the last reading, so a failed convergence records the
    true state instead of echoing the expectation.

    ``not_converged_at_s`` outcomes: immediate success -> ``None``; late
    success -> when the loop last read the old state (the lower bound on the
    convergence, from the loop's own previous round, not modelled from the
    cadence); budget expiry -> the last round, a lower bound that never
    resolved. ``wait_until`` parity holds: the probe always runs at least
    once, and probe exceptions propagate (terminal, not retried).
    ``poll_interval_s`` deliberately echoes the input into the result: the
    result is a self-contained evidence payload, so the cadence must travel
    with the record.
    """
    return _await_reading(
        lambda: probe_reachable(probe, proto, target_ip, tcp_port=tcp_port, udp_port=udp_port),
        want=want,
        budget_s=budget_s,
        interval_s=interval_s,
        sleep=sleep,
        monotonic=monotonic,
    )
