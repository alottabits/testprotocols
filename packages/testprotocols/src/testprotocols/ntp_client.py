"""NTP / Client template.

Defines the abstract contract for NTP client operations including
date retrieval, date setting, and time synchronisation.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class NtpClient(Protocol):
    """Abstract contract for NTP client operations."""

    def get_date(self) -> str | None:
        """Return the current date/time string from the device."""
        ...

    def set_date(self, opt: str, date_string: str) -> bool:
        """Set the device date/time using *opt* and *date_string*."""
        ...

    def execute_time_sync(self, time_server: str) -> str:
        """Synchronise device time against *time_server* and return status."""
        ...
