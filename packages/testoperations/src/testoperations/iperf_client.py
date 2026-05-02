"""iPerf client operations — compose iperf_client + iperf_server templates.

Receives resolved ``iperf_client`` and ``iperf_server`` template instances
from the caller.  The thin wrapper ``stop_iperf`` is deleted — step
definitions call the template method directly.
"""

from __future__ import annotations

from typing import Any


def start_iperf(
    iperf_client: Any,
    iperf_server: Any,
    port: int,
    time: int = 10,
    udp: bool = False,
    ip_version: int = 4,
) -> dict[str, Any]:
    """Start an iPerf session: receiver first, then sender.

    Returns a dict containing PIDs and log file paths for both sides:
    ``sender_pid``, ``sender_log``, ``receiver_pid``, ``receiver_log``.

    *iperf_client* and *iperf_server* are typed ``Any`` because the existing
    operation calls ``start_sender`` / ``start_receiver``, which are not part
    of the :class:`IperfClient` / :class:`IperfServer` protocol surfaces
    (``start_traffic_sender`` / ``start_traffic_receiver`` are). Pre-existing
    tech debt; logic is not modified here.
    """
    receiver_result = iperf_server.start_receiver(port, time=time, udp=udp, ip_version=ip_version)
    sender_result = iperf_client.start_sender(port, time=time, udp=udp, ip_version=ip_version)

    # Unpack (pid, log_file) tuples if the template returns them; otherwise
    # store the raw return value under _pid and _log keys.
    try:
        receiver_pid, receiver_log = receiver_result
    except (TypeError, ValueError):
        receiver_pid = receiver_result
        receiver_log = None

    try:
        sender_pid, sender_log = sender_result
    except (TypeError, ValueError):
        sender_pid = sender_result
        sender_log = None

    return {
        "sender_pid": sender_pid,
        "sender_log": sender_log,
        "receiver_pid": receiver_pid,
        "receiver_log": receiver_log,
    }
