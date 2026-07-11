"""Traffic / IperfClient template.

Defines the abstract contract for iperf client operations including
sending traffic and collecting logs.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class IperfClient(Protocol):
    """Abstract contract for iperf client (traffic sender) operations."""

    def start_traffic_sender(
        self,
        host: str,
        traffic_port: int,
        bandwidth: int | None = None,
        bind_to_ip: str | None = None,
        direction: str | None = None,
        ip_version: int | None = None,
        udp_protocol: bool = False,
        time: int = 10,
        client_port: int | None = None,
        udp_only: bool | None = None,
        reverse: bool = False,
        omit_s: int | None = None,
        json_output: bool = False,
        window: str | None = None,
    ) -> tuple[int, str]:
        """Start an iperf traffic sender towards *host* on *traffic_port*.

        Typed option parameters (each defaults to "absent": no flag emitted):

        - ``reverse``: iperf3 reverse mode (``-R``) — the listening receiver
          transmits; the sender still initiates the connection.
        - ``omit_s``: skip the first N seconds (``-O <n>``, the TCP slow-start
          ramp); omitted seconds extend the wall clock and are excluded from
          the end-of-test summary.
        - ``json_output``: machine-readable output (``--json``).
        - ``window``: pin the socket buffer (``-w <size>``, e.g. ``"8M"``) on
          BOTH ends — iperf3 forwards it to the server in the test-parameter
          exchange. Pinning disables OS receive/send autotuning; the effective
          value is capped by ``net.core.rmem_max``/``wmem_max`` (NOT
          ``tcp_rmem``/``tcp_wmem``), so the host must be provisioned
          accordingly.

        ``direction`` is DEPRECATED: a raw CLI fragment appended verbatim
        after the typed flags. Kept as an escape hatch only; use the typed
        parameters instead.

        Returns a tuple of (pid, log_file_path).
        """
        ...

    def stop_traffic(self, pid: int | None = None) -> bool:
        """Stop a running iperf traffic sender.

        Parameters
        ----------
        pid:
            Process ID to stop.  If *None*, stop the most recently started sender.
        """
        ...

    def get_iperf_logs(self, log_file: str) -> str:
        """Return the iperf log contents from *log_file*."""
        ...
