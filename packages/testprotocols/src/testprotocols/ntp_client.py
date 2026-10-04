"""NTP / Client template.

Defines the abstract contract for NTP client operations including
date retrieval, date setting, and time synchronisation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class NtpClient(Protocol):
    """Abstract contract for NTP client operations."""

    def get_date(self) -> str | None:
        """Deprecated: use :meth:`read_date`, which returns a ``datetime``.

        Returns the current date/time string from the device, in the device's own format
        (``None`` when it cannot be read). A driver keeps returning that text until the
        removal step (it warns with ``warn_renamed("get_date", "read_date")``).
        """
        ...

    def read_date(self) -> datetime | None:
        """Return the device's current date and time, or ``None`` when it cannot be read.

        The value is naive, in the device's local time, unless the device reports its UTC
        offset; then it is aware.
        """
        ...

    def set_date(self, opt: str, date_string: str) -> bool:
        """Deprecated: use :meth:`set_date_time`.

        Sets the device date/time using *opt* and *date_string*. A driver keeps this form until
        the removal step and warns with ``warn_renamed("set_date", "set_date_time")``; no
        caller was seen to pass an *opt* other than the set-the-date flag.
        """
        ...

    def set_date_time(self, value: datetime) -> bool:
        """Set the device's date and time to *value*; ``True`` when the device took it.

        A naive *value* is in the device's local time; an aware one is converted to it.
        """
        ...

    def execute_time_sync(self, time_server: str) -> str:
        """Synchronise device time against *time_server* and return status."""
        ...
