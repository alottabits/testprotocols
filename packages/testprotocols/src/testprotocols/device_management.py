"""Device management template.

Defines the abstract contract for querying runtime health and operational
state of a managed device, including uptime, memory, processes, and logs.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from testprotocols._compat import deprecated
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

    @deprecated(
        "Deprecated: use read_memory_utilization. Removal not before the first "
        "release 6 months after the release that deprecates it.",
        category=None,
    )
    def get_memory_utilization(self) -> dict[str, int]:
        """Return the figures of ``read_memory_utilization()``: memory utilization in bytes,
        keyed by metric name (``total``, ``used``, ``free`` and, when reported, ``shared``,
        ``cache``, ``available``).

        Deprecated: use :meth:`read_memory_utilization`. Removal not before the first release 6
        months after the release that deprecates it.
        """
        ...

    def read_memory_utilization(self) -> MemoryUtilization:
        """Return the device's memory figures, in bytes."""
        ...

    @deprecated(
        "Deprecated: use read_running_processes. Removal not before the first release "
        "6 months after the release that deprecates it.",
        category=None,
    )
    def get_running_processes(self, ps_options: str = "-A") -> list[Any]:  # type: ignore[explicit-any]  # released signature kept until removal
        """Return the list of running processes using the given ps options.

        For the default ``"-A"`` on a procps host each entry holds the fields of a
        ``read_running_processes()`` record (``pid``, ``tty``, ``time`` as
        ``[DD-]hh:mm:ss``, ``cmd``). Other options give the driver's released output.
        *ps_options* has no typed replacement: no caller was seen to pass one, and
        :meth:`read_running_processes` lists every process.

        Deprecated: use :meth:`read_running_processes`. Removal not before the first release 6
        months after the release that deprecates it.
        """
        ...

    def read_running_processes(self) -> list[ProcessInfo]:
        """Return every process running on the device (``ps -A`` on a Linux host)."""
        ...

    def get_board_logs(self, timeout: int = 300) -> str:
        """Return the board system log as a string, waiting up to *timeout* seconds."""
        ...

    @deprecated(
        "Deprecated: use read_log_entries. Removal not before the first release 6 "
        "months after the release that deprecates it.",
        category=None,
    )
    def read_event_logs(self) -> list[dict[str, Any]]:  # type: ignore[explicit-any]  # released signature kept until removal
        """Return the structured event log entries (``priority``, ``date``, ``hostname``,
        ``tag``, ``content``).

        The released output also carries the lines the driver's parser could not read
        (``{"unparsable": line}``), which :meth:`read_log_entries` leaves out. For a parsed line,
        the released entry holds the fields of an ``EventLogEntry`` (``date`` is its *timestamp*,
        ``content`` its *message*).

        Deprecated: use :meth:`read_log_entries`. Removal not before the first release 6 months
        after the release that deprecates it.
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
