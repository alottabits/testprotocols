"""Tests for testoperations.device_management module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from testoperations.device_management import wait_for_reboot_completion
from testprotocols.device_health import DeviceHealth
from testprotocols.models.device_management import (
    CpuLoad,
    EventLogEntry,
    MemoryUtilization,
    ProcessInfo,
)

# ---------------------------------------------------------------------------
# wait_for_reboot_completion
# ---------------------------------------------------------------------------


class TestWaitForRebootCompletion:
    def test_polls_until_online_returns_true_after_false(self) -> None:
        mgmt = MagicMock()
        # First goes offline, then comes back online
        mgmt.is_online.side_effect = [True, False, False, True]

        wait_for_reboot_completion(mgmt, timeout=5)
        assert mgmt.is_online.call_count >= 3

    def test_returns_when_starting_offline_then_online(self) -> None:
        mgmt = MagicMock()
        mgmt.is_online.side_effect = [False, True]

        wait_for_reboot_completion(mgmt, timeout=5)
        assert mgmt.is_online.call_count >= 2


def test_a_health_only_fake_that_never_comes_back_raises() -> None:
    """The widened operation keeps its other outcome: no return within the budget raises."""

    class NeverBack:
        def is_online(self) -> bool:
            return False

        def get_seconds_uptime(self) -> float:
            return 1.0

        def read_cpu_load(self) -> CpuLoad:
            return CpuLoad(None, None)

        def read_memory_utilization(self) -> MemoryUtilization:
            return MemoryUtilization(1, 0, 1)

        def read_running_processes(self) -> list[ProcessInfo]:
            return []

        def read_log_entries(self) -> list[EventLogEntry]:
            return []

    with pytest.raises(TimeoutError):
        wait_for_reboot_completion(NeverBack(), timeout=0)


def test_accepts_a_health_only_fake() -> None:
    """A fake with the six DeviceHealth members and nothing host-shaped is accepted (design M38)."""

    class HealthOnly:
        def __init__(self) -> None:
            self.calls = 0

        def is_online(self) -> bool:
            self.calls += 1
            return self.calls != 1  # offline on the first poll, then online

        def get_seconds_uptime(self) -> float:
            return 1.0

        def read_cpu_load(self) -> CpuLoad:
            return CpuLoad(None, None)

        def read_memory_utilization(self) -> MemoryUtilization:
            return MemoryUtilization(1, 0, 1)

        def read_running_processes(self) -> list[ProcessInfo]:
            return []

        def read_log_entries(self) -> list[EventLogEntry]:
            return []

    fake = HealthOnly()
    assert isinstance(fake, DeviceHealth)
    wait_for_reboot_completion(fake, timeout=5)
