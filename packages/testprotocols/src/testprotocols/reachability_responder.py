"""Reachability responder template — the answerer counterpart to ``NetworkProbe``.

``NetworkProbe`` *sends* reachability probes; a peer being probed must *answer*
them or a "blocked" verdict is indistinguishable from "no listener". This
capability stands up those answerers on the target's test interface:

* **TCP** — a listener that accepts connections (a ``tcp_can_connect`` connect
  probe completes the handshake on accept).
* **UDP** — an echo responder (a content-based ``udp_can_reach`` probe sends a
  token and is reachable iff it is echoed back).

ICMP needs no responder (the kernel answers echo requests). The pairing is
explicit and 1:1:

    NetworkProbe.tcp_can_connect  <->  ReachabilityResponder.start_tcp_responder
    NetworkProbe.udp_can_reach    <->  ReachabilityResponder.start_udp_responder
    NetworkProbe.icmp_can_reach   <->  (none — kernel)

Vendor-neutral contract; the listener mechanism (sockets / ``socat`` / a service)
lives entirely in the per-plugin impl, exactly as ``NetworkProbe`` impls do.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ReachabilityResponder(Protocol):
    """Abstract contract for standing up / tearing down reachability responders."""

    def start_tcp_responder(self, port: int) -> None:
        """Start a TCP responder on *port* that accepts connections.

        A connect-only ``NetworkProbe.tcp_can_connect`` probe completes its
        handshake against this listener, so an open path reads as reachable.
        """
        ...

    def start_udp_responder(self, port: int) -> None:
        """Start a UDP echo responder on *port*.

        Reflects every datagram it receives back to the sender, so a peer's
        content-based ``NetworkProbe.udp_can_reach`` probe gets its token echoed
        when the path is open — making "blocked" distinguishable from
        "no listener" on the connectionless protocol.
        """
        ...

    def stop(self, port: int | None = None) -> None:
        """Stop the responders on *port* (both protocols); ``None`` stops all.

        No-op if none is running.
        """
        ...
