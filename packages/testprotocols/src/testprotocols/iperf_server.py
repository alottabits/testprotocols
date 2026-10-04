"""Traffic / IperfServer template.

Defines the abstract contract for iperf server operations including
receiving traffic and collecting logs.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.networking import IpFamily


@runtime_checkable
class IperfServer(Protocol):
    """Abstract contract for iperf server (traffic receiver) operations."""

    def start_traffic_receiver(
        self,
        traffic_port: int,
        bind_to_ip: str | None = None,
        ip_version: IpFamily | int | None = None,
        udp_only: bool | None = None,
    ) -> tuple[int, str]:
        """Start an iperf traffic receiver on *traffic_port*.

        *ip_version* is an :class:`~testprotocols.models.IpFamily` (``V4 = 4``, ``V6 = 6``) or
        ``None`` to leave the version to the tool; a plain ``int`` is the released spelling
        and narrows to ``IpFamily`` in a later release (see ``IperfClient``).

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
