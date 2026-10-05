"""NTP / Client template.

Defines the abstract contract for NTP client operations including
date retrieval, date setting, and time synchronisation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from testprotocols._compat import deprecated


@runtime_checkable
class NtpClient(Protocol):
    """Abstract contract for NTP client operations."""

    @deprecated(
        "Deprecated: use read_date. Removal not before the first release 6 months "
        "after the release that deprecates it.",
        category=None,
    )
    def get_date(self) -> str | None:
        """Return the current date/time string from the device, in the device's own format
        (``None`` when it cannot be read).

        Deprecated: use :meth:`read_date`. Removal not before the first release 6 months after
        the release that deprecates it.
        """
        ...

    def read_date(self) -> datetime | None:
        """Return the device's current date and time, or ``None`` when it cannot be read.

        ``None`` means the device gave no date to read: its date command produced no output
        that holds a date and time (the case in which the released ``get_date`` returned
        ``None``). It never means "not synchronised": an unsynchronised clock still has a
        date, which is returned.

        The value is naive, in the device's local time, unless the device reports its UTC
        offset; then it is aware.
        """
        ...

    @deprecated(
        "Deprecated: use set_date_time. Removal not before the first release 6 months "
        "after the release that deprecates it.",
        category=None,
    )
    def set_date(self, opt: str, date_string: str) -> bool:
        """Set the device date/time using *opt* and *date_string*.

        No caller was seen to pass an *opt* other than the set-the-date flag.

        Deprecated: use :meth:`set_date_time`. Removal not before the first release 6 months after
        the release that deprecates it.
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
