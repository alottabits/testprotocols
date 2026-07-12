"""Tests for testoperations.waiting (poll-until-converge mechanics)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from testoperations.waiting import probe_reachable, wait_for_reachability, wait_until


class FakeClock:
    """Deterministic monotonic + sleep pair: sleeping advances the clock."""

    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def test_wait_until_true_immediately_never_sleeps() -> None:
    clock = FakeClock()
    assert (
        wait_until(
            lambda: True, budget_s=10, interval_s=1, sleep=clock.sleep, monotonic=clock.monotonic
        )
        is True
    )
    assert clock.sleeps == []


def test_wait_until_converges_after_polls() -> None:
    clock = FakeClock()
    verdicts = iter([False, False, True])
    assert (
        wait_until(
            lambda: next(verdicts),
            budget_s=10,
            interval_s=2,
            sleep=clock.sleep,
            monotonic=clock.monotonic,
        )
        is True
    )
    assert clock.sleeps == [2, 2]


def test_wait_until_budget_expiry_returns_false() -> None:
    clock = FakeClock()
    calls = 0

    def never() -> bool:
        nonlocal calls
        calls += 1
        return False

    assert (
        wait_until(never, budget_s=5, interval_s=2, sleep=clock.sleep, monotonic=clock.monotonic)
        is False
    )
    # Polls at t=0/2/4 (pre-deadline) and once more at t=6 where the deadline check exits.
    assert clock.sleeps == [2, 2, 2]
    assert calls == 4


@pytest.mark.parametrize(
    ("proto", "method", "args"),
    [
        ("icmp", "icmp_can_reach", ("10.0.0.9",)),
        ("tcp", "tcp_can_connect", ("10.0.0.9", 5201)),
        ("udp", "udp_can_reach", ("10.0.0.9", 5201)),
    ],
)
def test_probe_reachable_dispatch(proto: str, method: str, args: tuple[Any, ...]) -> None:
    probe = MagicMock()
    getattr(probe, method).return_value = True
    assert probe_reachable(probe, proto, "10.0.0.9") is True
    getattr(probe, method).assert_called_once_with(*args)


def test_probe_reachable_custom_ports() -> None:
    probe = MagicMock()
    probe_reachable(probe, "tcp", "10.0.0.9", tcp_port=8080)
    probe.tcp_can_connect.assert_called_once_with("10.0.0.9", 8080)
    probe_reachable(probe, "udp", "10.0.0.9", udp_port=6000)
    probe.udp_can_reach.assert_called_once_with("10.0.0.9", 6000)


def test_probe_reachable_unknown_proto_raises() -> None:
    with pytest.raises(ValueError, match="unsupported probe protocol"):
        probe_reachable(MagicMock(), "gre", "10.0.0.9")


def test_wait_for_reachability_waits_for_wanted_verdict() -> None:
    clock = FakeClock()
    probe = MagicMock()
    probe.icmp_can_reach.side_effect = [True, True, False]  # deny converges on 3rd poll
    assert (
        wait_for_reachability(
            probe,
            "icmp",
            "10.0.0.9",
            want=False,
            budget_s=30,
            interval_s=5,
            sleep=clock.sleep,
            monotonic=clock.monotonic,
        )
        is True
    )
    assert clock.sleeps == [5, 5]


def test_wait_for_reachability_budget_expiry() -> None:
    clock = FakeClock()
    probe = MagicMock()
    probe.tcp_can_connect.return_value = False
    assert (
        wait_for_reachability(
            probe,
            "tcp",
            "10.0.0.9",
            want=True,
            budget_s=4,
            interval_s=2,
            sleep=clock.sleep,
            monotonic=clock.monotonic,
        )
        is False
    )
