"""Network endpoint operations — polling helpers over the ``NetworkEndpoint`` protocol.

A ``NetworkEndpoint`` returns the address a peer would use to reach a
device. Right after disruptive events (reboot, link bounce, netem
blackout/recovery) the underlying interface may transiently have no
IPv4 lease, so the endpoint returns an empty string. These operations
let scenarios coordinate over that recovery without hardcoding
polling loops in step definitions.
"""

from __future__ import annotations

import time

from testprotocols.network_endpoint import NetworkEndpoint


def wait_for_endpoint_ready(
    endpoint: NetworkEndpoint,
    timeout_s: int,
    poll_s: float = 1.0,
) -> str:
    """Poll *endpoint* until ``get_ipv4_addr()`` returns a non-empty string.

    Returns the resolved IPv4 address. Raises ``TimeoutError`` if no
    address is observed within *timeout_s* seconds. Transient exceptions
    from the underlying capability (e.g. a console glitch mid-recovery)
    are caught and retried — only the deadline ends the loop.

    Use this after disruptive events whose precise recovery moment is
    unobservable: e.g. a CPE reboot drops the LAN DHCP lease, and the
    client regains connectivity at some point during the CPE's boot.
    The data-plane probes that follow have to wait for *that* moment,
    not just for the CPE's management plane to come back up.
    """
    deadline = time.monotonic() + timeout_s
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            ip = endpoint.get_ipv4_addr()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            ip = ""
        if ip:
            return ip
        time.sleep(poll_s)
    if last_error is not None:
        raise TimeoutError(
            f"network endpoint did not become ready within {timeout_s}s "
            f"(last error: {last_error!r})"
        )
    raise TimeoutError(
        f"network endpoint did not become ready within {timeout_s}s "
        f"(get_ipv4_addr kept returning empty)"
    )
