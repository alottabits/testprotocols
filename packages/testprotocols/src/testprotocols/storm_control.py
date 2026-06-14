"""Per-port broadcast/multicast/unknown-unicast storm-control thresholds."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.switch import StormControlConfig


@runtime_checkable
class StormControl(Protocol):
    """Abstract contract for per-port storm control.

    A product that exposes storm control only in a controller UI (no API) raises
    unsupported-capability.
    """

    def set_config(self, config: StormControlConfig) -> None:
        """Apply storm-control thresholds for ``config.port``."""
        ...

    def get_config(self, port: str) -> StormControlConfig:
        """Return storm-control thresholds for *port*."""
        ...
