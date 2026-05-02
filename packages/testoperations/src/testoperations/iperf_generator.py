"""iPerf generator operations — traffic generation presets and multi-generator stop.

Receives resolved ``iperf_generator`` template instances from the caller.
Thin wrappers (start_traffic, stop_traffic, stop_all_traffic, run_traffic)
are deleted — step definitions call the template method directly.
"""

from __future__ import annotations

from testprotocols.iperf_generator import IperfGenerator
from testprotocols.models.traffic import TrafficResult, TrafficSpec


def _assert_distinct_peers(peer_a: IperfGenerator, peer_b: IperfGenerator) -> None:
    """Reject self-loop peer configurations.

    Bidirectional traffic between peers that resolve to the same host would
    collide on the iperf3 server pool (both clients target the same server
    on the same port), producing "server is busy" errors for one side.
    Callers must supply distinct peers.
    """
    if peer_a.server_ip == peer_b.server_ip:
        raise ValueError(
            f"peer_a and peer_b both resolve to {peer_a.server_ip!r}. "
            "Bidirectional traffic between the same host is not supported — "
            "each peer must be at a distinct address."
        )


def _flow_spec(
    destination_peer: IperfGenerator,
    bandwidth_mbps: float,
    dscp: int,
    duration_s: int,
    protocol: str,
) -> TrafficSpec:
    """Build a TrafficSpec whose destination is *destination_peer*'s server_ip."""
    return TrafficSpec(
        destination=destination_peer.server_ip,
        bandwidth_mbps=bandwidth_mbps,
        protocol=protocol,
        dscp=dscp,
        duration_s=duration_s,
    )


def saturate_link(
    peer_a: IperfGenerator,
    peer_b: IperfGenerator,
    a_to_b_mbps: float,
    b_to_a_mbps: float | None = None,
    dscp: int = 0,
    duration_s: int = 120,
    protocol: str = "udp",
) -> dict[str, str]:
    """Saturate the network path between two peer generators with bidirectional traffic.

    The caller passes two generator objects; each generator is asked to send
    to the other peer. Addresses never cross the step-def ↔ operation boundary
    — each peer resolves its counterparty's destination via the peer's own
    :attr:`server_ip` template property.

    - ``peer_a.start_traffic`` with destination = ``peer_b.server_ip`` (a→b)
    - ``peer_b.start_traffic`` with destination = ``peer_a.server_ip`` (b→a)

    Pass ``a_to_b_mbps`` alone for symmetric load (both directions at the same
    rate). Supply ``b_to_a_mbps`` to model asymmetric loads such as a broadband
    link with faster downstream than upstream. Works for any testbed topology
    with two or more generators — the caller picks the pair that bracket the
    path to saturate.

    :param peer_a: First generator (source of a→b, destination of b→a).
    :param peer_b: Second generator (source of b→a, destination of a→b).
    :param a_to_b_mbps: Bandwidth in Mbps for the a→b flow (and for b→a when
        *b_to_a_mbps* is omitted, giving symmetric load).
    :param b_to_a_mbps: Bandwidth in Mbps for the b→a flow. Defaults to
        *a_to_b_mbps* for symmetric load.
    :param dscp: DSCP code point for both flows (default 0 = best-effort).
    :param duration_s: Flow duration in seconds (default 120).
    :param protocol: ``"udp"`` (default) or ``"tcp"``.
    :return: ``{"a_to_b": <flow_id_on_peer_a>, "b_to_a": <flow_id_on_peer_b>}``.
    :raises ValueError: if ``peer_a.server_ip == peer_b.server_ip``.
    """
    _assert_distinct_peers(peer_a, peer_b)
    if b_to_a_mbps is None:
        b_to_a_mbps = a_to_b_mbps
    a_to_b = peer_a.start_traffic(_flow_spec(peer_b, a_to_b_mbps, dscp, duration_s, protocol))
    b_to_a = peer_b.start_traffic(_flow_spec(peer_a, b_to_a_mbps, dscp, duration_s, protocol))
    return {"a_to_b": a_to_b, "b_to_a": b_to_a}


def stop_all_generators(
    generators: list[IperfGenerator],
) -> list[dict[str, TrafficResult]]:
    """Stop all traffic flows on each generator in *generators*.

    *generators* is a list of resolved iperf_generator template instances.

    Returns a list of ``stop_all_traffic`` results (each a mapping of
    flow_id to ``TrafficResult``), one per generator, in the same order.
    """
    results: list[dict[str, TrafficResult]] = []
    for gen in generators:
        results.append(gen.stop_all_traffic())
    return results
