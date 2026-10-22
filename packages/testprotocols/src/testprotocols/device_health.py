"""Device health — the read-only health a device publishes about itself.

The reads a closed product publishes without a host shell: whether it is
online, its uptime, its processor load, its memory, its process list and its
event log. Split off ``DeviceManagement`` (``SPLITS.md`` 2026-10-20), which
inherits it, so every implementer of the host-shaped protocol satisfies this
base while a closed product composes the base alone — the decision recorded
in ``GAPS.md`` 2026-06-11 and the ``RoutingRead`` precedent (a read-only
protocol split off ``Router``).

In scope: online check, uptime, processor load, memory, processes, event log.

Out of scope: the host-shaped reads (``get_file_content``, ``get_board_logs``,
``get_boottime_log`` — see ``device_management``), the levers (reboot, factory
reset — see ``device_lifecycle``), identity (see ``device_info``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.device_management import (
    CpuLoad,
    EventLogEntry,
    MemoryUtilization,
    ProcessInfo,
)


@runtime_checkable
class DeviceHealth(Protocol):
    """Abstract contract for the read-only health of a device."""

    def is_online(self) -> bool:
        """Return True if the device is reachable and operational."""
        ...

    def get_seconds_uptime(self) -> float:
        """Return the device uptime in seconds; raises ``NotSupportedError`` where the family
        publishes no uptime."""
        ...

    def read_cpu_load(self) -> CpuLoad:
        """Return the device's processor load.

        ``percent`` is the family's processor-usage figure and ``load_average_1m`` the
        kernel's one-minute load average, each ``None`` where the family publishes no such
        figure; a family that publishes neither raises ``NotSupportedError``.
        """
        ...

    def read_memory_utilization(self) -> MemoryUtilization:
        """Return the device's memory figures, in bytes; raises ``NotSupportedError`` where
        the family publishes none."""
        ...

    def read_running_processes(self) -> list[ProcessInfo]:
        """Return every process running on the device (``ps -A`` on a Linux host); raises
        ``NotSupportedError`` where the family publishes no process list."""
        ...

    def read_log_entries(self) -> list[EventLogEntry]:
        """Return the entries of the device's event log, oldest first. A line the driver
        cannot parse as a syslog entry is left out."""
        ...
