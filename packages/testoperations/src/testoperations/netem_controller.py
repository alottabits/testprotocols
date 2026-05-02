"""Netem controller operations — preset library and transient event injection.

Receives a resolved ``netem`` template instance from the caller.  Thin
wrappers (set_impairment_profile, clear, set_interface_profile,
get_impairment_profile) are deleted — step definitions call the template
method directly.
"""

from __future__ import annotations

from testprotocols.models.impairment import ImpairmentProfile
from testprotocols.netem_controller import NetemController

# ---------------------------------------------------------------------------
# Built-in impairment presets
# ---------------------------------------------------------------------------

_PRESETS: dict[str, ImpairmentProfile] = {
    "clean": ImpairmentProfile(latency_ms=0, jitter_ms=0, loss_percent=0.0),
    "dsl": ImpairmentProfile(latency_ms=20, jitter_ms=5, loss_percent=0.1, bandwidth_limit_mbps=20),
    "cable": ImpairmentProfile(
        latency_ms=10, jitter_ms=2, loss_percent=0.05, bandwidth_limit_mbps=100
    ),
    "lte": ImpairmentProfile(
        latency_ms=50, jitter_ms=10, loss_percent=0.2, bandwidth_limit_mbps=50
    ),
    "3g": ImpairmentProfile(latency_ms=100, jitter_ms=20, loss_percent=1.0, bandwidth_limit_mbps=7),
    "satellite": ImpairmentProfile(
        latency_ms=600, jitter_ms=50, loss_percent=0.5, bandwidth_limit_mbps=10
    ),
    "degraded": ImpairmentProfile(latency_ms=200, jitter_ms=50, loss_percent=5.0),
    "lossy": ImpairmentProfile(latency_ms=50, jitter_ms=10, loss_percent=10.0),
}


def apply_preset(netem_controller: NetemController, preset_name: str) -> None:
    """Apply a named impairment preset.

    Built-in presets: ``clean``, ``dsl``, ``cable``, ``lte``, ``3g``,
    ``satellite``, ``degraded``, ``lossy``.

    Raises ``ValueError`` if *preset_name* is not recognised.
    """
    if preset_name not in _PRESETS:
        raise ValueError(f"unknown preset {preset_name!r}; available: {sorted(_PRESETS)}")
    netem_controller.set_impairment_profile(_PRESETS[preset_name])


def inject_blackout(netem_controller: NetemController, duration_ms: int) -> None:
    """Inject a complete connectivity blackout of *duration_ms* milliseconds."""
    netem_controller.inject_transient("blackout", duration_ms)


def inject_brownout(
    netem_controller: NetemController,
    duration_ms: int,
    loss_percent: float = 50.0,
) -> None:
    """Inject a partial connectivity brownout of *duration_ms* ms.

    *loss_percent* controls how much traffic is dropped during the event.
    """
    netem_controller.inject_transient("brownout", duration_ms, loss_percent=loss_percent)


def inject_latency_spike(
    netem_controller: NetemController,
    duration_ms: int,
    latency_ms: int = 500,
) -> None:
    """Inject a latency spike of *latency_ms* ms lasting *duration_ms* ms."""
    netem_controller.inject_transient("latency_spike", duration_ms, latency_ms=latency_ms)


def inject_packet_storm(
    netem_controller: NetemController,
    duration_ms: int,
    duplicate_percent: float = 100.0,
) -> None:
    """Inject a packet storm (heavy duplication) of *duration_ms* ms."""
    netem_controller.inject_transient(
        "packet_storm", duration_ms, duplicate_percent=duplicate_percent
    )
