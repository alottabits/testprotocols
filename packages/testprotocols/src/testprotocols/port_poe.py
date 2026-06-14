"""Per-port PoE configuration and status read."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.switch import PoePortStatus, PoePriority


@runtime_checkable
class PortPoe(Protocol):
    """Abstract contract for per-port PoE."""

    def set_enabled(self, port: str, enabled: bool) -> None:
        """Enable or disable PoE on *port*."""
        ...

    def set_priority(self, port: str, priority: PoePriority) -> None:
        """Set PoE priority on *port*. Products without a priority knob raise
        unsupported-capability."""
        ...

    def get_status(self, port: str) -> PoePortStatus:
        """Return live PoE status/draw for *port*."""
        ...
