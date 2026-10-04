"""Resolve a driver member across a deprecated rename.

A published operation keeps working through a rename's deprecation period
(CONTRIBUTING.md, "Versioning"): it calls the member's new name when the
driver has it and falls back to the old name otherwise, so a driver that has
not migrated yet still works and a migrated driver never reaches its own
deprecated alias. The fallback is removed in the release that removes the
old name.

Each accessor casts the member to a callable Protocol of the contract's exact
shape; ``tests/test_renamed_accessor_conformance.py`` checks those shapes
against the contracts with the type checkers.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, cast

from testprotocols.models import (
    IperfProcess,
    IpFamily,
    ParameterValue,
    TransientEvent,
    parse_window_size,
)


class _Member(Protocol):
    """A driver member, called with whatever arguments its released signature takes."""

    def __call__(self, *args: object, **kwargs: object) -> object: ...


def _callable_member(driver: object, name: str) -> _Member:
    member: object = getattr(driver, name)
    if not callable(member):
        raise TypeError(f"{type(driver).__name__}.{name} is not callable")
    return member


def _new_member(driver: object, name: str) -> _Member | None:
    """*driver*'s *name* member when it has one, else ``None``."""
    if getattr(driver, name, None) is None:
        return None
    return _callable_member(driver, name)


# --- IperfClient / IperfServer: start_traffic_* -> start_*_session --------------------


class StartSenderSession(Protocol):
    """``IperfClient.start_sender_session``: the new name's shape."""

    def __call__(
        self,
        host: str,
        traffic_port: int,
        *,
        bandwidth: int | None = ...,
        bind_to_ip: str | None = ...,
        ip_version: IpFamily | None = ...,
        udp_protocol: bool = ...,
        time: int = ...,
        client_port: int | None = ...,
        udp_only: bool | None = ...,
        reverse: bool = ...,
        omit_s: int | None = ...,
        json_output: bool = ...,
        window_bytes: int | None = ...,
        parallel: int | None = ...,
        datagram_bytes: int | None = ...,
        report_interval_s: int | None = ...,
    ) -> IperfProcess: ...


class StartTrafficSender(Protocol):
    """``IperfClient.start_traffic_sender``: the old name, with the keywords operations pass."""

    def __call__(
        self,
        host: str,
        traffic_port: int,
        bandwidth: int | None = ...,
        bind_to_ip: str | None = ...,
        ip_version: IpFamily | int | None = ...,
        udp_protocol: bool = ...,
        time: int = ...,
        client_port: int | None = ...,
        udp_only: bool | None = ...,
        reverse: bool = ...,
        omit_s: int | None = ...,
        json_output: bool = ...,
        window: str | None = ...,
        parallel: int | None = ...,
        datagram_bytes: int | None = ...,
        report_interval_s: int | None = ...,
    ) -> tuple[int, str]: ...


class StartReceiverSession(Protocol):
    """``IperfServer.start_receiver_session``: the new name's shape."""

    def __call__(
        self,
        traffic_port: int,
        *,
        bind_to_ip: str | None = ...,
        ip_version: IpFamily | None = ...,
        udp_only: bool | None = ...,
    ) -> IperfProcess: ...


class StartTrafficReceiver(Protocol):
    """``IperfServer.start_traffic_receiver``: the old name, with its released signature."""

    def __call__(
        self,
        traffic_port: int,
        bind_to_ip: str | None = ...,
        ip_version: IpFamily | int | None = ...,
        udp_only: bool | None = ...,
    ) -> tuple[int, str]: ...


def start_sender_session_of(driver: object) -> StartSenderSession | None:
    """Return a driver's ``start_sender_session`` (the new name), or ``None`` without it."""
    member = _new_member(driver, "start_sender_session")
    # The callable is checked; its shape is the IperfClient contract's.
    return None if member is None else cast(StartSenderSession, member)


def start_traffic_sender_of(driver: object) -> StartTrafficSender:
    """Return a driver's ``start_traffic_sender`` (the old name, its released signature)."""
    return cast(StartTrafficSender, _callable_member(driver, "start_traffic_sender"))


def start_receiver_session_of(driver: object) -> StartReceiverSession | None:
    """Return a driver's ``start_receiver_session`` (the new name), or ``None`` without it."""
    member = _new_member(driver, "start_receiver_session")
    return None if member is None else cast(StartReceiverSession, member)


def start_traffic_receiver_of(driver: object) -> StartTrafficReceiver:
    """Return a driver's ``start_traffic_receiver`` (the old name, its released signature)."""
    return cast(StartTrafficReceiver, _callable_member(driver, "start_traffic_receiver"))


def start_sender_session(
    driver: object,
    host: str,
    traffic_port: int,
    *,
    bandwidth: int | None = None,
    time: int = 10,
    reverse: bool = False,
    omit_s: int | None = None,
    json_output: bool = False,
    window: str | None = None,
    parallel: int | None = None,
) -> IperfProcess:
    """Start an iperf sender on *driver* with the names it has; return the process.

    A driver with ``start_sender_session`` gets the window as ``window_bytes`` (the size text
    *window*, ``"8M"``, parsed with ``parse_window_size``: malformed text raises
    ``ValueError`` before anything starts). A driver with only ``start_traffic_sender`` gets
    exactly the released call, *window* as given.
    """
    start = start_sender_session_of(driver)
    if start is not None:
        window_bytes = None if window is None else parse_window_size(window)
        return start(
            host,
            traffic_port,
            bandwidth=bandwidth,
            time=time,
            reverse=reverse,
            omit_s=omit_s,
            json_output=json_output,
            window_bytes=window_bytes,
            parallel=parallel,
        )
    pid, log_file = start_traffic_sender_of(driver)(
        host,
        traffic_port,
        bandwidth=bandwidth,
        time=time,
        reverse=reverse,
        omit_s=omit_s,
        json_output=json_output,
        window=window,
        parallel=parallel,
    )
    return IperfProcess(pid, log_file)


def start_receiver_session(driver: object, traffic_port: int) -> IperfProcess:
    """Start an iperf receiver on *driver* with the name it has; return the process."""
    start = start_receiver_session_of(driver)
    if start is not None:
        return start(traffic_port)
    pid, log_file = start_traffic_receiver_of(driver)(traffic_port)
    return IperfProcess(pid, log_file)


# --- NetemController: inject_transient -> inject_event --------------------------------


class InjectEvent(Protocol):
    """``NetemController.inject_event``: the new name's shape."""

    def __call__(self, event: TransientEvent, duration_ms: int) -> None: ...


class InjectTransient(Protocol):
    """``NetemController.inject_transient``: the old name, with its released signature."""

    def __call__(self, event: str, duration_ms: int, **kwargs: float | int) -> None: ...


def inject_event_of(driver: object) -> InjectEvent | None:
    """Return a driver's ``inject_event`` (the new name), or ``None`` without it."""
    member = _new_member(driver, "inject_event")
    return None if member is None else cast(InjectEvent, member)


def inject_transient_of(driver: object) -> InjectTransient:
    """Return a driver's ``inject_transient`` (the old name, its released signature)."""
    return cast(InjectTransient, _callable_member(driver, "inject_transient"))


def inject(
    driver: object,
    event: TransientEvent,
    duration_ms: int,
    released_kwargs: dict[str, float | int],
) -> None:
    """Inject *event* on *driver* with the name it has.

    A driver with ``inject_event`` gets the typed event. A driver with only
    ``inject_transient`` gets exactly the call the operation made before the rename:
    ``event.event_name`` and the operation's own *released_kwargs*.
    """
    inject_new = inject_event_of(driver)
    if inject_new is not None:
        inject_new(event, duration_ms)
        return
    inject_transient_of(driver)(event.event_name, duration_ms, **released_kwargs)


# --- Tr069Server: GPV -> get_parameter_values -----------------------------------------


class GetParameterValues(Protocol):
    """``Tr069Server.get_parameter_values``: the new name's shape."""

    def __call__(
        self,
        names: Sequence[str],
        *,
        timeout: int | None = ...,
        cpe_id: str | None = ...,
    ) -> list[ParameterValue]: ...


class Gpv(Protocol):
    """``Tr069Server.GPV``: the old name, with the keywords operations pass.

    The released return (``list[dict[str, Any]]``) is not read by any operation, so it is
    typed ``object`` here.
    """

    def __call__(
        self,
        param: str | list[str],
        timeout: int | None = ...,
        cpe_id: str | None = ...,
    ) -> object: ...


def get_parameter_values_of(driver: object) -> GetParameterValues | None:
    """Return a driver's ``get_parameter_values`` (the new name), or ``None`` without it."""
    member = _new_member(driver, "get_parameter_values")
    return None if member is None else cast(GetParameterValues, member)


def gpv_of(driver: object) -> Gpv:
    """Return a driver's ``GPV`` (the old name, its released signature)."""
    return cast(Gpv, _callable_member(driver, "GPV"))


def get_parameter_value(driver: object, name: str, *, cpe_id: str | None = None) -> None:
    """Run GetParameterValues for the one parameter *name* with the name *driver* has.

    A driver with ``get_parameter_values`` gets ``[name]``; a driver with only ``GPV`` gets
    exactly the released call (``name`` as a ``str``). Errors propagate; the result is not
    read. *name* must be one ``str`` (``TypeError`` otherwise, before any call).
    """
    if not isinstance(cast(object, name), str):  # callers are not all type-checked
        raise TypeError(f"get_parameter_value takes one parameter name, not {name!r}")
    get_new = get_parameter_values_of(driver)
    if get_new is not None:
        get_new([name], cpe_id=cpe_id)
        return
    gpv_of(driver)(name, cpe_id=cpe_id)
