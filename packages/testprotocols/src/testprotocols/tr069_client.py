"""TR-069 CPE client template.

Defines the abstract contract for TR-069 client operations on a CPE
device — the CPE-side counterpart to the ACS-side ``Tr069Server``
Protocol. Covers connection status, log retrieval, the CPE's own
identity, the ACS configuration and the ability to provoke an inform.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.tr069 import AcsConfig


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
        """Provoke an inform session now, outside the periodic schedule.

        A lever where the family publishes a trigger for it, through the client's own
        interface; raises ``NotSupportedError`` where the family publishes none. Confirmed
        by ``is_tr069_connected`` and the test-bed ACS's inform record.
        """
        ...

    def set_acs(self, config: AcsConfig) -> None:
        """Write the ACS configuration; paired read ``get_acs``.

        The two passwords are required on a write when the ACS authenticates and ``None`` on
        every read; the written values are confirmed by ``is_tr069_connected`` after the next
        inform.

        A write rejected at any step raises naming the step; the driver puts nothing back. The
        state is then the as-found ACS configuration where the family commits atomically,
        otherwise the steps applied before the rejection.
        """
        ...

    def get_acs(self) -> AcsConfig:
        """Return the ACS configuration, both passwords ``None``."""
        ...
