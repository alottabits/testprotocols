"""TR-069 CPE client template.

Defines the abstract contract for TR-069 client operations on a CPE
device — the CPE-side counterpart to the ACS-side ``Tr069Server``
Protocol. Covers connection status, log retrieval, the CPE's own
identity, and the ability to force an immediate Inform.
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

    def get_id(self) -> str:
        """Return the CPE's TR-069 device identifier as known to the ACS.

        Per CWMP §A.3.3.1 this is the ``OUI-ProductClass-SerialNumber``
        tuple the CPE uses in its Inform header. The ACS uses this as
        its primary key when storing the per-CPE record. Implementations
        should source the value from the CPE itself (e.g. the CWMP
        daemon's UCI config) rather than from external inventory, so
        the value is always self-consistent with what the ACS sees.
        """
        ...

    def force_inform(self) -> None:
        """Trigger an immediate Inform to the ACS, bypassing the periodic schedule.

        Used to make queued ACS-side tasks execute promptly instead of
        waiting for the next periodic Inform window (typically 300s).
        Implementations route through whatever CWMP daemon ipc the CPE
        provides (``ubus call tr069 inform`` on prplOS/iCWMPD, the
        equivalent on other daemons).
        """
        ...
