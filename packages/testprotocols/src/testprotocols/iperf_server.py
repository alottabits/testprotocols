"""Traffic / IperfServer template.

Defines the abstract contract for iperf server operations including
receiving traffic and collecting logs.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.networking import IpVersion


@runtime_checkable
class IperfServer(Protocol):
    """Abstract contract for iperf server (traffic receiver) operations."""

    def start_traffic_receiver(
        self,
        traffic_port: int,
        bind_to_ip: str | None = None,
        ip_version: IpVersion | int | None = None,
        udp_only: bool | None = None,
    ) -> tuple[int, str]:
        """Start an iperf traffic receiver on *traffic_port*.

        *ip_version* is an :class:`~testprotocols.models.IpVersion`; the released ``int``
        (``4`` or ``6``) is deprecated: the driver converts it with ``coerce_ip_version``
        and warns. ``None`` leaves the version to the tool.

        Returns a tuple of (pid, log_file_path).
        """
        ...

    def stop_traffic(self, pid: int | None = None) -> bool:
        """Stop a running iperf traffic receiver.

        Parameters
        ----------
        pid:
            Process ID to stop.  If *None*, stop the most recently started receiver.
        """
        ...

    def get_iperf_logs(self, log_file: str) -> str:
        """Return the iperf log contents from *log_file*."""
        ...
