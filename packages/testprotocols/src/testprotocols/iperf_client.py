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
    ) -> tuple[int, str]:
        """Start an iperf traffic sender towards *host* on *traffic_port*.

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
