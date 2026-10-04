"""Device management template.

Defines the abstract contract for querying runtime health and operational
state of a managed device, including uptime, memory, processes, and logs.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from testprotocols.models.device_management import (
    EventLogEntry,
    MemoryUtilization,
    ProcessInfo,
)


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
        """Deprecated name of :meth:`read_memory_utilization`.

        Returns ``read_memory_utilization().as_dict()``: memory utilization in bytes, keyed
        by metric name (``total``, ``used``, ``free`` and, when reported, ``shared``,
        ``cache``, ``available``); the driver warns with
        ``warn_renamed("get_memory_utilization", "read_memory_utilization")``.
        """
        ...

    def read_memory_utilization(self) -> MemoryUtilization:
        """Return the device's memory figures, in bytes."""
        ...

    def get_running_processes(self, ps_options: str = "-A") -> list[Any]:  # type: ignore[explicit-any]  # released signature kept until removal
        """Deprecated name of :meth:`read_running_processes`.

        Returns the list of running processes using the given ps options. For the default
        ``"-A"`` on a procps host that is
        ``[p.as_dict() for p in read_running_processes()]``; the driver warns with
        ``warn_renamed("get_running_processes", "read_running_processes")``. Other
        options keep the driver's released output until the removal step.

        *ps_options* other than the default ``"-A"`` is deprecated with no typed replacement
        (no caller was seen to pass one, and :meth:`read_running_processes` lists every
        process): a driver warns when it differs from ``"-A"``.
        """
        ...

    def read_running_processes(self) -> list[ProcessInfo]:
        """Return every process running on the device (``ps -A`` on a Linux host)."""
        ...

    def get_board_logs(self, timeout: int = 300) -> str:
        """Return the board system log as a string, waiting up to *timeout* seconds."""
        ...

    def read_event_logs(self) -> list[dict[str, Any]]:  # type: ignore[explicit-any]  # released signature kept until removal
        """Deprecated: use :meth:`read_log_entries`, which returns typed entries.

        Returns the structured event log entries (``priority``, ``date``, ``hostname``,
        ``tag``, ``content``). A driver keeps its released output here until the removal
        step (it warns with ``warn_renamed("read_event_logs", "read_log_entries")``): that
        output also carries the lines its parser could not read (``{"unparsable": line}``),
        which :meth:`read_log_entries` leaves out. For a parsed line,
        ``EventLogEntry.as_dict()`` is the released entry.
        """
        ...

    def read_log_entries(self) -> list[EventLogEntry]:
        """Return the entries of the device's event log, oldest first. A line the driver
        cannot parse as a syslog entry is left out."""
        ...

    def get_boottime_log(self) -> list[str]:
        """Return the boot-time log as a list of log lines."""
        ...

    def get_file_content(self, fname: str, timeout: int = 30) -> str:
        """Return the content of the named file from the device filesystem."""
        ...
