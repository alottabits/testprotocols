"""SNMP / Client template.

Defines the abstract contract for SNMP client operations.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SnmpClient(Protocol):
    """Abstract contract for SNMP client operations."""

    def execute_snmp_command(self, snmp_command: str, timeout: int = 30) -> str:
        """Execute an SNMP command and return the output string."""
        ...
