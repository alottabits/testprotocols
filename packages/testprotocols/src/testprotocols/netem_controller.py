"""Traffic / NetemController template.

Defines the abstract contract for network emulation (netem) impairment
control on device interfaces.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols._compat import deprecated
from testprotocols.models.impairment import ImpairmentProfile, TransientEvent


@runtime_checkable
class NetemController(Protocol):
    """Abstract contract for netem-based network impairment control."""

    def set_impairment_profile(self, profile: ImpairmentProfile | dict[str, object]) -> None:
        """Apply *profile* as the default impairment on all managed interfaces.

        A ``dict`` of the profile's field names is deprecated. The annotation narrows to
        ``ImpairmentProfile`` in a later release.
        """
        ...

    def set_interface_profile(
        self, interface: str, profile: ImpairmentProfile | dict[str, object]
    ) -> None:
        """Apply *profile* as the impairment on a specific *interface*.

        A ``dict`` is deprecated, as for :meth:`set_impairment_profile`.
        """
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

    @deprecated(
        "Deprecated: use inject_event. Removal not before the first release 6 months "
        "after the release that deprecates it.",
        category=None,
    )
    def inject_transient(self, event: str, duration_ms: int, **kwargs: float | int) -> None:
        """Inject a transient impairment *event* (``"blackout"``, ``"brownout"``,
        ``"latency_spike"`` or ``"packet_storm"``) lasting *duration_ms* milliseconds, with
        the event's keyword options.

        Each word is the ``event_name`` of a :data:`~testprotocols.models.TransientEvent`.

        Deprecated: use :meth:`inject_event`. Removal not before the first release 6 months after
        the release that deprecates it.
        """
        ...

    def inject_event(self, event: TransientEvent, duration_ms: int) -> None:
        """Apply *event* to every managed interface for *duration_ms* milliseconds, then
        restore each interface's previous profile; returns at once (the restore is
        scheduled). An event field left ``None`` takes the driver's default; a field the
        driver cannot apply raises ``ValueError`` before anything changes."""
        ...
