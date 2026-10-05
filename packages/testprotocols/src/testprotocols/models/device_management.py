"""Device health records: memory, processes and the event log.

The typed forms of what ``DeviceManagement.get_memory_utilization``, ``get_running_processes``
and ``read_event_logs`` returned as dicts. Every field comes from the released docstrings and
what the released implementers return (``free``, ``ps -A`` and a BSD-syslog parse of the device
log).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import IntEnum


@dataclass(frozen=True)
class MemoryUtilization:
    """A device's memory figures, in bytes.

    *total_bytes*, *used_bytes* and *free_bytes* are always reported; *shared_bytes*,
    *cache_bytes* (buffers and page cache) and *available_bytes* (an estimate of what can be
    allocated without swapping) are reported together or not at all (``None``), as ``free``
    reports them. Every figure is not negative, and *used_bytes* and *free_bytes* are at
    most *total_bytes*.
    """

    total_bytes: int
    used_bytes: int
    free_bytes: int
    shared_bytes: int | None = None
    cache_bytes: int | None = None
    available_bytes: int | None = None


@dataclass(frozen=True)
class ProcessInfo:
    """One running process: its *pid*, controlling terminal (*tty*, ``None`` when it has
    none), the CPU time it has used (*cpu_time*, whole seconds, not negative) and its
    *command*."""

    pid: int
    tty: str | None
    cpu_time: timedelta
    command: str


class SyslogSeverity(IntEnum):
    """A syslog message severity (RFC 5424, section 6.2.1; the registry closes the set)."""

    EMERGENCY = 0
    ALERT = 1
    CRITICAL = 2
    ERROR = 3
    WARNING = 4
    NOTICE = 5
    INFORMATIONAL = 6
    DEBUG = 7


@dataclass(frozen=True)
class EventLogEntry:
    """One entry of a device's event log, in BSD syslog form (RFC 3164).

    *timestamp* is the device's own text (``"Oct 11 22:14:15"``): the form carries no year,
    so it is not turned into a ``datetime``. *hostname* is the reporting host, *tag* the
    program or facility tag (``None`` when the line has none) and *message* the rest of the
    line. *priority* is the ``<PRI>`` value (facility * 8 + severity, 0 to 191) when the line
    carries one, else ``None``.
    """

    timestamp: str
    hostname: str
    tag: str | None
    message: str
    priority: int | None = None

    @property
    def severity(self) -> SyslogSeverity | None:
        """The severity carried in *priority*, or ``None`` when the line has no priority."""
        return None if self.priority is None else SyslogSeverity(self.priority % 8)
