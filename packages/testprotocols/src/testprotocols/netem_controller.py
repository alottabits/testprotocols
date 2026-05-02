"""Traffic / NetemController template.

Defines the abstract contract for network emulation (netem) impairment
control on device interfaces.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.impairment import ImpairmentProfile


@runtime_checkable
class NetemController(Protocol):
    """Abstract contract for netem-based network impairment control."""

    def set_impairment_profile(self, profile: ImpairmentProfile | dict) -> None:
        """Apply *profile* as the default impairment on all managed interfaces."""
        ...

    def set_interface_profile(self, interface: str, profile: ImpairmentProfile | dict) -> None:
        """Apply *profile* as the impairment on a specific *interface*."""
        ...

    def get_interface_profile(self, interface: str) -> ImpairmentProfile:
        """Return the current impairment profile for *interface*."""
        ...

    def get_interface_profiles(self) -> dict[str, ImpairmentProfile]:
        """Return a mapping of interface names to their current impairment profiles."""
        ...

    def clear(self) -> None:
        """Remove all active impairments from all managed interfaces."""
        ...

    def inject_transient(self, event: str, duration_ms: int, **kwargs: float | int) -> None:
        """Inject a transient impairment *event* lasting *duration_ms* milliseconds."""
        ...
