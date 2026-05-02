"""Device management template.

Defines the abstract contract for querying runtime health and operational
state of a managed device, including uptime, memory, processes, and logs.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DeviceManagement(Protocol):
    """Abstract contract for device management and health monitoring operations."""

    def get_seconds_uptime(self) -> float:
        """Return the device uptime in seconds."""
        ...

    def is_online(self) -> bool:
        """Return True if the device is reachable and operational."""
        ...

    def get_load_avg(self) -> float:
        """Return the current 1-minute load average of the device."""
        ...

    def get_memory_utilization(self) -> dict[str, int]:
        """Return memory utilization in bytes, keyed by metric name."""
        ...

    def get_running_processes(self, ps_options: str = "-A") -> list[Any]:
        """Return the list of running processes using the given ps options."""
        ...

    def get_board_logs(self, timeout: int = 300) -> str:
        """Return the board system log as a string, waiting up to *timeout* seconds."""
        ...

    def read_event_logs(self) -> list[dict[str, Any]]:
        """Return structured event log entries from the device."""
        ...

    def get_boottime_log(self) -> list[str]:
        """Return the boot-time log as a list of log lines."""
        ...

    def get_file_content(self, fname: str, timeout: int = 30) -> str:
        """Return the content of the named file from the device filesystem."""
        ...
