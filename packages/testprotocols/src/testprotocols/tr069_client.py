"""TR-069 CPE client template.

Defines the abstract contract for TR-069 client operations on a CPE device,
including connection status and log retrieval.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Tr069Client(Protocol):
    """Abstract contract for TR-069 client operations on a CPE device."""

    def is_tr069_connected(self) -> bool:
        """Return True if the CPE has an active TR-069 connection to the ACS."""
        ...

    def get_tr069_log(self) -> list[str]:
        """Return the TR-069 client log as a list of log lines."""
        ...
