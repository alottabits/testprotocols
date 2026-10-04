"""Network impairment profile data model and transient impairment events."""

from __future__ import annotations

import warnings
from collections.abc import Mapping
from dataclasses import dataclass, fields
from typing import ClassVar, cast

from testprotocols.models import _checks


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


_PROFILE_REQUIRED = ("latency_ms", "jitter_ms", "loss_percent")


def coerce_impairment_profile(
    profile: ImpairmentProfile | Mapping[str, object], *, what: str
) -> ImpairmentProfile:
    """Return *profile* as an :class:`ImpairmentProfile`, for a driver's ``profile`` parameter.

    A profile is returned as is. A mapping of the profile's field names (the released dict
    form) is deprecated: it warns (``DeprecationWarning``, pointing at the driver's caller)
    and converts, the values passed through unchanged. A missing ``latency_ms``,
    ``jitter_ms`` or ``loss_percent``, or a key that names no field, raises ``ValueError``
    (before any warning); any other type raises ``TypeError``.
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
    missing = [name for name in _PROFILE_REQUIRED if name not in data]
    if missing:
        raise ValueError(f"{what}: the dict lacks {missing}")
    warnings.warn(
        f"{what}: a dict is deprecated; pass an ImpairmentProfile",
        DeprecationWarning,
        stacklevel=3,
    )
    return ImpairmentProfile(
        latency_ms=cast(int, data["latency_ms"]),
        jitter_ms=cast(int, data["jitter_ms"]),
        loss_percent=cast(float, data["loss_percent"]),
        bandwidth_limit_mbps=cast("int | None", data.get("bandwidth_limit_mbps")),
        reorder_percent=cast(float, data.get("reorder_percent", 0.0)),
        corrupt_percent=cast(float, data.get("corrupt_percent", 0.0)),
        duplicate_percent=cast(float, data.get("duplicate_percent", 0.0)),
    )


def _ms(owner: str, name: str, value: object) -> None:
    _checks.optional_count(owner, name, value)


def _percent(owner: str, name: str, value: object) -> None:
    _checks.optional_number(owner, name, value, high=100)


def _given(**values: float | int | None) -> dict[str, float | int]:
    return {key: value for key, value in values.items() if value is not None}


@dataclass(frozen=True)
class Blackout:
    """Every packet is lost for the event's duration (100 % loss); the latency and jitter
    in force are kept."""

    event_name: ClassVar[str] = "blackout"

    def as_kwargs(self) -> dict[str, float | int]:
        """The released ``inject_transient`` keyword arguments: none."""
        return {}


@dataclass(frozen=True)
class Brownout:
    """A degraded link: the given one-way *latency_ms*, *jitter_ms* and *loss_percent*
    (0 to 100). A field left ``None`` takes the driver's own default for a brownout."""

    event_name: ClassVar[str] = "brownout"

    latency_ms: int | None = None
    jitter_ms: int | None = None
    loss_percent: float | None = None

    def __post_init__(self) -> None:
        _ms("Brownout", "latency_ms", self.latency_ms)
        _ms("Brownout", "jitter_ms", self.jitter_ms)
        _percent("Brownout", "loss_percent", self.loss_percent)

    def as_kwargs(self) -> dict[str, float | int]:
        """The released ``inject_transient`` keyword arguments: ``latency_ms``,
        ``jitter_ms`` and ``loss_percent``, each only when given."""
        return _given(
            latency_ms=self.latency_ms, jitter_ms=self.jitter_ms, loss_percent=self.loss_percent
        )


@dataclass(frozen=True)
class LatencySpike:
    """A temporary high latency: *latency_ms* (one-way) and *jitter_ms* during the spike;
    the loss in force is kept. A field left ``None`` takes the driver's own default."""

    event_name: ClassVar[str] = "latency_spike"

    latency_ms: int | None = None
    jitter_ms: int | None = None

    def __post_init__(self) -> None:
        _ms("LatencySpike", "latency_ms", self.latency_ms)
        _ms("LatencySpike", "jitter_ms", self.jitter_ms)

    def as_kwargs(self) -> dict[str, float | int]:
        """The released ``inject_transient`` keyword arguments: the released implementers
        read the spike latency as ``spike_latency_ms``, and ``jitter_ms``."""
        return _given(spike_latency_ms=self.latency_ms, jitter_ms=self.jitter_ms)


@dataclass(frozen=True)
class PacketStorm:
    """A burst of disturbed packets: *loss_percent* and *duplicate_percent* (0 to 100) with
    the given *latency_ms* and *jitter_ms*. A field left ``None`` takes the driver's own
    default; a driver that cannot apply a given field raises rather than ignoring it."""

    event_name: ClassVar[str] = "packet_storm"

    loss_percent: float | None = None
    latency_ms: int | None = None
    jitter_ms: int | None = None
    duplicate_percent: float | None = None

    def __post_init__(self) -> None:
        _percent("PacketStorm", "loss_percent", self.loss_percent)
        _ms("PacketStorm", "latency_ms", self.latency_ms)
        _ms("PacketStorm", "jitter_ms", self.jitter_ms)
        _percent("PacketStorm", "duplicate_percent", self.duplicate_percent)

    def as_kwargs(self) -> dict[str, float | int]:
        """The released ``inject_transient`` keyword arguments, each only when given."""
        return _given(
            loss_percent=self.loss_percent,
            latency_ms=self.latency_ms,
            jitter_ms=self.jitter_ms,
            duplicate_percent=self.duplicate_percent,
        )


TransientEvent = Blackout | Brownout | LatencySpike | PacketStorm
"""A timed impairment event for ``NetemController.inject_event``. Each event's
``event_name`` is its released ``inject_transient`` word and ``as_kwargs()`` the released
keyword arguments the implementers read."""


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
