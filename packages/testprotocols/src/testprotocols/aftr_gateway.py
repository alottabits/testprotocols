"""AFTR / Gateway template.

Defines the abstract contract for Address Family Transition Router (AFTR)
gateway operations used in DS-Lite deployments.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class AftrGateway(Protocol):
    """Abstract contract for AFTR gateway operations."""

    def configure_aftr(self) -> None:
        """Apply the AFTR configuration on the gateway."""
        ...

    def restart_aftr_process(self) -> None:
        """Restart the AFTR process on the gateway."""
        ...
