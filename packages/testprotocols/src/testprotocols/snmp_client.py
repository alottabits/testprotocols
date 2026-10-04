"""SNMP / Client template.

Defines the abstract contract for SNMP client operations.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SnmpClient(Protocol):
    """Abstract contract for SNMP client operations."""

    def execute_snmp_command(self, snmp_command: str, timeout: int = 30) -> str:
        """Deprecated: use :meth:`snmp_get` or :meth:`snmp_walk`.

        Executes an SNMP command line and returns the output string. A driver keeps it until
        the removal step and warns (``DeprecationWarning``). The typed members cover the
        commands callers were seen to run (``snmpget``, ``snmpwalk``, ``snmpset``,
        ``snmpbulkget``); any other command has no successor, because a whole command line
        stops being part of the contract.
        """
        ...

    def snmp_get(
        self,
        host: str,
        oid: str,
        community: str,
        *,
        timeout_s: int = 10,
        retries: int = 3,
        command_timeout: int = 30,
    ) -> str:
        """Read the object *oid* from the SNMP agent at *host* (protocol version 2c, numeric
        object names) with *community*, and return the tool's output.

        *timeout_s* and *retries* are the per-request wait and retry count; *command_timeout*
        is how long the call waits for the tool to finish, in seconds.
        """
        ...

    def snmp_walk(
        self,
        host: str,
        oid: str,
        community: str,
        *,
        timeout_s: int = 100,
        retries: int = 3,
        command_timeout: int = 30,
    ) -> str:
        """Walk the subtree under *oid* of the SNMP agent at *host* (an empty *oid* walks from
        the root); the parameters and the return are as for :meth:`snmp_get`."""
        ...

    def snmp_set(
        self,
        host: str,
        oid: str,
        community: str,
        value: str,
        value_type: str,
        *,
        timeout_s: int = 10,
        retries: int = 3,
        command_timeout: int = 30,
    ) -> str:
        """Write *value* to the object *oid* of the SNMP agent at *host* and return the tool's
        output.

        *value_type* is the tool's single-letter type code (``"i"`` integer, ``"s"`` string,
        ``"x"`` hex string, ...); a *value* beginning ``0x`` is sent as hex. The other
        parameters are as for :meth:`snmp_get`.
        """
        ...

    def snmp_bulk_get(
        self,
        host: str,
        oid: str,
        community: str,
        *,
        non_repeaters: int = 0,
        max_repetitions: int = 10,
        timeout_s: int = 100,
        retries: int = 3,
        command_timeout: int = 30,
    ) -> str:
        """Bulk-read from *oid* of the SNMP agent at *host* (an empty *oid* starts at the
        root) and return the tool's output.

        *non_repeaters* and *max_repetitions* are the bulk request's own counts; the other
        parameters are as for :meth:`snmp_get`.
        """
        ...
