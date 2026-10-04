"""Device health records: memory, processes and the event log.

The typed forms of what ``DeviceManagement.get_memory_utilization``, ``get_running_processes``
and ``read_event_logs`` returned as dicts. Each record's ``as_dict()`` is the released entry
shape, with the same keys, value types and text formats: the whole released return for memory,
and for processes on a procps host (``ps -A``); for the event log, the entry of each parsed line
(the released output also holds the lines the parser could not read, which no record holds).
Every field comes from the released docstrings and what the released implementers return
(``free``, ``ps -A`` and a BSD-syslog parse of the device log).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import IntEnum
from typing import cast

from testprotocols.models import _checks


@dataclass(frozen=True)
class MemoryUtilization:
    """A device's memory figures, in bytes.

    *total_bytes*, *used_bytes* and *free_bytes* are always reported; *shared_bytes*,
    *cache_bytes* (buffers and page cache) and *available_bytes* (an estimate of what can be
    allocated without swapping) are reported together or not at all (``None``), as ``free``
    reports them. *used_bytes* and *free_bytes* are at most *total_bytes*; anything else
    raises ``ValueError``.
    """

    total_bytes: int
    used_bytes: int
    free_bytes: int
    shared_bytes: int | None = None
    cache_bytes: int | None = None
    available_bytes: int | None = None

    def __post_init__(self) -> None:
        for name in ("total_bytes", "used_bytes", "free_bytes"):
            _checks.count("MemoryUtilization", name, getattr(self, name))
        extra = ("shared_bytes", "cache_bytes", "available_bytes")
        for name in extra:
            _checks.optional_count("MemoryUtilization", name, getattr(self, name))
        given = [name for name in extra if getattr(self, name) is not None]
        if given and len(given) != len(extra):
            raise ValueError(
                f"MemoryUtilization: {sorted(set(extra) - set(given))} must be given with {given}"
            )
        for name in ("used_bytes", "free_bytes"):
            if getattr(self, name) > self.total_bytes:
                raise ValueError(f"MemoryUtilization.{name} exceeds total_bytes")

    def as_dict(self) -> dict[str, int]:
        """The released ``get_memory_utilization`` dict: ``total``, ``used``, ``free`` and,
        when reported, ``shared``, ``cache`` and ``available``, in that order, in bytes."""
        figures = {
            "total": self.total_bytes,
            "used": self.used_bytes,
            "free": self.free_bytes,
            "shared": self.shared_bytes,
            "cache": self.cache_bytes,
            "available": self.available_bytes,
        }
        return {key: value for key, value in figures.items() if value is not None}


def _format_cpu_time(value: timedelta) -> str:
    """procps' ``TIME`` column: ``[DD-]hh:mm:ss``."""
    seconds = int(value.total_seconds())
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, secs = divmod(rest, 60)
    clock = f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{days}-{clock}" if days else clock


@dataclass(frozen=True)
class ProcessInfo:
    """One running process: its *pid*, controlling terminal (*tty*, ``None`` when it has
    none), the CPU time it has used (*cpu_time*, whole seconds) and its *command*.

    ``as_dict()`` round-trips a procps ``ps -A`` entry exactly (its ``TIME`` column is
    ``[DD-]hh:mm:ss``); another ``ps`` prints other columns and formats."""

    pid: int
    tty: str | None
    cpu_time: timedelta
    command: str

    def __post_init__(self) -> None:
        _checks.count("ProcessInfo", "pid", self.pid)
        _checks.optional_text("ProcessInfo", "tty", self.tty)
        if not isinstance(cast(object, self.cpu_time), timedelta):
            raise TypeError(f"ProcessInfo.cpu_time takes a timedelta, not {self.cpu_time!r}")
        if self.cpu_time < timedelta(0) or self.cpu_time.microseconds:
            raise ValueError(
                f"ProcessInfo.cpu_time must be a whole, non-negative number of seconds: "
                f"{self.cpu_time!r}"
            )
        _checks.text("ProcessInfo", "command", self.command)

    def as_dict(self) -> dict[str, object]:
        """The released ``get_running_processes`` entry for ``ps -A``: ``pid``, ``tty``
        (``None`` for no terminal), ``time`` (``[DD-]hh:mm:ss``) and ``cmd``."""
        return {
            "pid": self.pid,
            "tty": self.tty,
            "time": _format_cpu_time(self.cpu_time),
            "cmd": self.command,
        }


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


_MAX_PRIORITY = 23 * 8 + 7  # facility 23 (local7), severity 7 (debug)


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

    def __post_init__(self) -> None:
        _checks.text("EventLogEntry", "timestamp", self.timestamp)
        _checks.text("EventLogEntry", "hostname", self.hostname)
        _checks.optional_text("EventLogEntry", "tag", self.tag)
        _checks.text("EventLogEntry", "message", self.message)
        if self.priority is not None:
            _checks.count("EventLogEntry", "priority", self.priority)
            if self.priority > _MAX_PRIORITY:
                raise ValueError(
                    f"EventLogEntry.priority must be 0 to {_MAX_PRIORITY}: {self.priority}"
                )

    @property
    def severity(self) -> SyslogSeverity | None:
        """The severity carried in *priority*, or ``None`` when the line has no priority."""
        return None if self.priority is None else SyslogSeverity(self.priority % 8)

    def as_dict(self) -> dict[str, object]:
        """The released ``read_event_logs`` entry of a parsed line: ``priority``, ``date``,
        ``hostname``, ``tag`` and ``content``."""
        return {
            "priority": self.priority,
            "date": self.timestamp,
            "hostname": self.hostname,
            "tag": self.tag,
            "content": self.message,
        }
