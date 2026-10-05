"""Network impairment profile data model and transient impairment events."""

from __future__ import annotations

import warnings
from collections.abc import Mapping
from dataclasses import dataclass, fields
from typing import ClassVar, cast


@dataclass
class ImpairmentProfile:
    """Holds parameters describing a network impairment scenario (latency, jitter, loss, etc.)."""

    latency_ms: int
    jitter_ms: int
    loss_percent: float
    bandwidth_limit_mbps: int | None = None
    reorder_percent: float = 0.0
    corrupt_percent: float = 0.0
    duplicate_percent: float = 0.0


def coerce_impairment_profile(
    profile: ImpairmentProfile | Mapping[str, object], *, what: str
) -> ImpairmentProfile:
    """Return *profile* as an :class:`ImpairmentProfile`, for a driver's ``profile`` parameter.

    A profile is returned as is. A mapping of the profile's field names (the released dict
    form) is deprecated: it warns (``DeprecationWarning``, pointing at the driver's caller)
    and converts. A missing field takes ``0`` (``None`` for ``bandwidth_limit_mbps``), as the
    released example implementer's conversion does. A key that names no field raises
    ``ValueError``; a value of the wrong type (``"20"``, a ``bool``) raises ``TypeError``;
    both before any warning. Any other argument type raises ``TypeError``.
    """
    given = cast(object, profile)
    if isinstance(given, ImpairmentProfile):
        return given
    if not isinstance(given, Mapping):
        raise TypeError(f"{what}: takes an ImpairmentProfile, not {given!r}")
    data = cast("Mapping[str, object]", given)
    known = {f.name for f in fields(ImpairmentProfile)}
    unknown = sorted(set(data) - known)
    if unknown:
        raise ValueError(f"{what}: the dict names no profile field {unknown}")
    for name in ("latency_ms", "jitter_ms", "bandwidth_limit_mbps"):
        value = data.get(name)
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
            raise TypeError(f"{what}: {name} takes an int, not {value!r}")
    for name in ("loss_percent", "reorder_percent", "corrupt_percent", "duplicate_percent"):
        value = data.get(name, 0.0)
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise TypeError(f"{what}: {name} takes a number, not {value!r}")
    warnings.warn(
        f"{what}: a dict is deprecated; pass an ImpairmentProfile",
        DeprecationWarning,
        stacklevel=3,
    )
    return ImpairmentProfile(
        latency_ms=cast(int, data.get("latency_ms", 0)),
        jitter_ms=cast(int, data.get("jitter_ms", 0)),
        loss_percent=cast(float, data.get("loss_percent", 0.0)),
        bandwidth_limit_mbps=cast("int | None", data.get("bandwidth_limit_mbps")),
        reorder_percent=cast(float, data.get("reorder_percent", 0.0)),
        corrupt_percent=cast(float, data.get("corrupt_percent", 0.0)),
        duplicate_percent=cast(float, data.get("duplicate_percent", 0.0)),
    )


@dataclass(frozen=True)
class Blackout:
    """Every packet is lost for the event's duration (100 % loss); the latency and jitter
    in force are kept."""

    event_name: ClassVar[str] = "blackout"


@dataclass(frozen=True)
class Brownout:
    """A degraded link: the given one-way *latency_ms* and *jitter_ms* (not negative) and
    *loss_percent* (0 to 100). A field left ``None`` takes the driver's own default for a
    brownout."""

    event_name: ClassVar[str] = "brownout"

    latency_ms: int | None = None
    jitter_ms: int | None = None
    loss_percent: float | None = None


@dataclass(frozen=True)
class LatencySpike:
    """A temporary high latency: *latency_ms* (one-way) and *jitter_ms* during the spike,
    not negative; the loss in force is kept. A field left ``None`` takes the driver's own
    default."""

    event_name: ClassVar[str] = "latency_spike"

    latency_ms: int | None = None
    jitter_ms: int | None = None


@dataclass(frozen=True)
class PacketStorm:
    """A burst of packet loss: *loss_percent* (0 to 100) with the given *latency_ms* and
    *jitter_ms* (not negative), as the released implementers apply a packet storm. A field
    left ``None`` takes the driver's own default.

    *duplicate_percent* (0 to 100) is optional and ``None`` (not requested) by default: the
    share of packets duplicated as well. No released implementer applies duplication; a
    driver that cannot apply a requested field raises ``ValueError`` rather than ignoring
    it."""

    event_name: ClassVar[str] = "packet_storm"

    loss_percent: float | None = None
    latency_ms: int | None = None
    jitter_ms: int | None = None
    duplicate_percent: float | None = None


TransientEvent = Blackout | Brownout | LatencySpike | PacketStorm
"""A timed impairment event for ``NetemController.inject_event``. Each event's
``event_name`` is its released ``inject_transient`` word."""


_EVENT_KEYS: dict[str, frozenset[str]] = {
    "blackout": frozenset(),
    "brownout": frozenset({"latency_ms", "jitter_ms", "loss_percent"}),
    "latency_spike": frozenset({"spike_latency_ms", "latency_ms", "jitter_ms"}),
    "packet_storm": frozenset({"loss_percent", "latency_ms", "jitter_ms", "duplicate_percent"}),
}


def _whole_ms(name: str, value: float | int | None) -> int | None:
    """A released millisecond value as an ``int`` (``500.0`` is ``500``)."""
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError(f"{name}: {value!r} is not a whole number of milliseconds")
        return int(value)
    return value


def transient_event(event: str, **kwargs: float | int) -> TransientEvent:
    """Return the typed event for a released ``inject_transient(event, duration_ms, **kwargs)``
    call: the converter a driver's deprecated ``inject_transient`` uses before it delegates to
    ``inject_event``. It does not warn: the driver warns with ``warn_renamed``.

    *event* is one of the released words (``blackout``, ``brownout``, ``latency_spike``,
    ``packet_storm``) and *kwargs* the keywords the released implementers read; for a spike,
    ``spike_latency_ms`` and the spelling ``latency_ms`` are both accepted, not together. An
    unknown event or keyword raises ``ValueError``, so a misspelt keyword is not ignored.
    """
    keys = _EVENT_KEYS.get(event)
    if keys is None:
        raise ValueError(f"transient event: {event!r} is not one of {sorted(_EVENT_KEYS)}")
    unknown = sorted(set(kwargs) - keys)
    if unknown:
        raise ValueError(f"transient event {event!r}: takes no {unknown}; takes {sorted(keys)}")
    get = kwargs.get
    if event == "blackout":
        return Blackout()
    if event == "brownout":
        return Brownout(
            latency_ms=_whole_ms("latency_ms", get("latency_ms")),
            jitter_ms=_whole_ms("jitter_ms", get("jitter_ms")),
            loss_percent=get("loss_percent"),
        )
    if event == "latency_spike":
        if "spike_latency_ms" in kwargs and "latency_ms" in kwargs:
            raise ValueError("transient event 'latency_spike': give spike_latency_ms only")
        latency = get("spike_latency_ms", get("latency_ms"))
        return LatencySpike(
            latency_ms=_whole_ms("latency_ms", latency),
            jitter_ms=_whole_ms("jitter_ms", get("jitter_ms")),
        )
    return PacketStorm(
        loss_percent=get("loss_percent"),
        latency_ms=_whole_ms("latency_ms", get("latency_ms")),
        jitter_ms=_whole_ms("jitter_ms", get("jitter_ms")),
        duplicate_percent=get("duplicate_percent"),
    )
