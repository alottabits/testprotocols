"""Netem controller operations — preset library and transient event injection.

Receives a resolved ``netem`` template instance from the caller.  Thin
wrappers (set_impairment_profile, clear, set_interface_profile,
get_impairment_profile) are deleted — step definitions call the template
method directly.
"""

from __future__ import annotations

from enum import StrEnum

from testprotocols.deprecation import coerce_enum
from testprotocols.models.impairment import (
    Blackout,
    Brownout,
    ImpairmentProfile,
    LatencySpike,
    PacketStorm,
)
from testprotocols.netem_controller import NetemController

from testoperations._renamed import inject

# ---------------------------------------------------------------------------
# Built-in impairment presets
# ---------------------------------------------------------------------------


class NetemPreset(StrEnum):
    """The built-in impairment presets :func:`apply_preset` knows."""

    CLEAN = "clean"
    DSL = "dsl"
    CABLE = "cable"
    LTE = "lte"
    THREE_G = "3g"
    SATELLITE = "satellite"
    DEGRADED = "degraded"
    LOSSY = "lossy"


_PRESETS: dict[NetemPreset, ImpairmentProfile] = {
    NetemPreset.CLEAN: ImpairmentProfile(latency_ms=0, jitter_ms=0, loss_percent=0.0),
    NetemPreset.DSL: ImpairmentProfile(
        latency_ms=20, jitter_ms=5, loss_percent=0.1, bandwidth_limit_mbps=20
    ),
    NetemPreset.CABLE: ImpairmentProfile(
        latency_ms=10, jitter_ms=2, loss_percent=0.05, bandwidth_limit_mbps=100
    ),
    NetemPreset.LTE: ImpairmentProfile(
        latency_ms=50, jitter_ms=10, loss_percent=0.2, bandwidth_limit_mbps=50
    ),
    NetemPreset.THREE_G: ImpairmentProfile(
        latency_ms=100, jitter_ms=20, loss_percent=1.0, bandwidth_limit_mbps=7
    ),
    NetemPreset.SATELLITE: ImpairmentProfile(
        latency_ms=600, jitter_ms=50, loss_percent=0.5, bandwidth_limit_mbps=10
    ),
    NetemPreset.DEGRADED: ImpairmentProfile(latency_ms=200, jitter_ms=50, loss_percent=5.0),
    NetemPreset.LOSSY: ImpairmentProfile(latency_ms=50, jitter_ms=10, loss_percent=10.0),
}


def apply_preset(netem_controller: NetemController, preset_name: NetemPreset | str) -> None:
    """Apply a named impairment preset.

    *preset_name* is a :class:`NetemPreset` (``clean``, ``dsl``, ``cable``, ``lte``, ``3g``,
    ``satellite``, ``degraded``, ``lossy``). A plain string naming one (``"dsl"``) is
    deprecated: it warns and converts.

    Raises ``ValueError`` if *preset_name* is not recognised (the message lists the legal
    names).
    """
    preset = coerce_enum(NetemPreset, preset_name, what="apply_preset(preset_name)")
    netem_controller.set_impairment_profile(_PRESETS[preset])


def inject_blackout(netem_controller: NetemController, duration_ms: int) -> None:
    """Inject a complete connectivity blackout of *duration_ms* milliseconds.

    Calls ``inject_event(Blackout(), duration_ms)``; a driver without ``inject_event`` gets
    the released ``inject_transient("blackout", duration_ms)``.
    """
    inject(netem_controller, Blackout(), duration_ms, {})


def inject_brownout(
    netem_controller: NetemController,
    duration_ms: int,
    loss_percent: float = 50.0,
) -> None:
    """Inject a partial connectivity brownout of *duration_ms* ms.

    *loss_percent* controls how much traffic is dropped during the event. Calls
    ``inject_event(Brownout(loss_percent=...), duration_ms)``; a driver without
    ``inject_event`` gets the released ``inject_transient`` call.
    """
    inject(
        netem_controller,
        Brownout(loss_percent=loss_percent),
        duration_ms,
        {"loss_percent": loss_percent},
    )


def inject_latency_spike(
    netem_controller: NetemController,
    duration_ms: int,
    latency_ms: int = 500,
) -> None:
    """Inject a latency spike of *latency_ms* ms lasting *duration_ms* ms.

    Calls ``inject_event(LatencySpike(latency_ms=...), duration_ms)``. A driver without
    ``inject_event`` gets the released ``inject_transient("latency_spike", duration_ms,
    latency_ms=...)`` call, unchanged: the released drivers read ``spike_latency_ms`` and so
    ignore *latency_ms* there (they apply their default, 500 ms).
    """
    inject(
        netem_controller,
        LatencySpike(latency_ms=latency_ms),
        duration_ms,
        {"latency_ms": latency_ms},
    )


def inject_packet_storm(
    netem_controller: NetemController,
    duration_ms: int,
    duplicate_percent: float | None = None,
    *,
    loss_percent: float | None = None,
) -> None:
    """Inject a packet storm of *duration_ms* ms: a burst of packet loss, as the released
    drivers apply it (*loss_percent*, when given; otherwise the driver's default).

    *duplicate_percent*, when given, also asks for that share of packets to be duplicated;
    no released driver applies duplication, and a driver that cannot raises. Calls
    ``inject_event(PacketStorm(...), duration_ms)``. A driver without ``inject_event`` gets
    the released ``inject_transient("packet_storm", duration_ms, duplicate_percent=...)``
    call (``100.0``, the released default, when not given; plus ``loss_percent`` when given).
    """
    released: dict[str, float | int] = {
        "duplicate_percent": 100.0 if duplicate_percent is None else duplicate_percent
    }
    if loss_percent is not None:
        released["loss_percent"] = loss_percent
    inject(
        netem_controller,
        PacketStorm(loss_percent=loss_percent, duplicate_percent=duplicate_percent),
        duration_ms,
        released,
    )
