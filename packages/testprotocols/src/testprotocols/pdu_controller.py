"""PDU / Controller template.

Defines the abstract contract for Power Distribution Unit controller
operations including power cycling.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PduController(Protocol):
    """Abstract contract for PDU controller operations."""

    def power_on(self) -> bool:
        """Power on the outlet and return True on success."""
        ...

    def power_off(self) -> bool:
        """Power off the outlet and return True on success."""
        ...

    def power_cycle(self) -> bool:
        """Power cycle the outlet and return True on success."""
        ...
