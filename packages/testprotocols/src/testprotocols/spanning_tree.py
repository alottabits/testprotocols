"""Spanning-tree configuration — global mode/priority + per-port guards."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.l2_common import StpMode, StpPortState
from testprotocols.models.switch import StpPortConfig


@runtime_checkable
class SpanningTree(Protocol):
    """Abstract contract for spanning-tree configuration and read."""

    def set_mode(self, mode: StpMode) -> None:
        """Set the global STP mode. RSTP-only products raise unsupported-capability on MSTP."""
        ...

    def get_mode(self) -> StpMode:
        """Return the active STP mode."""
        ...

    def set_bridge_priority(self, priority: int) -> None:
        """Set the bridge priority."""
        ...

    def set_port_config(self, config: StpPortConfig) -> None:
        """Apply per-port guard/edge/path-cost/priority for ``config.port``."""
        ...

    def get_port_config(self, port: str) -> StpPortConfig:
        """Return the per-port STP configuration for *port*."""
        ...

    def get_port_state(self, port: str) -> StpPortState:
        """Return the observed STP state for *port*."""
        ...
