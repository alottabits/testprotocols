"""Poll-until-converge waiting operations.

Distributed-system state (route propagation, policy pushes, log delivery) is
eventual, so tests observe it by polling a boolean signal until it reads the
wanted way or a time budget lapses. These are MECHANICS, not policies: the
budget, the interval, and what to do about a ``False`` verdict all live with
the caller — nothing here raises on expiry or decides pass/fail.

``probe_reachable`` / ``wait_for_reachability`` bind the skeleton to the
:class:`~testprotocols.network_probe.NetworkProbe` contract for the common
L3/L4 case. UDP verdicts are only meaningful when the target runs a responder
(see the protocol's docstring) — ensuring one is the caller's arrangement.

The module imports only testprotocols contracts — no devices, no vendor SDKs.
"""

from __future__ import annotations

import time
from collections.abc import Callable

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
