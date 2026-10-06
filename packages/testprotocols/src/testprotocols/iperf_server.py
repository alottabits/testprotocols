"""Traffic / IperfServer template.

Defines the abstract contract for iperf server operations including
receiving traffic and collecting logs.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols._compat import deprecated
from testprotocols.models.networking import IpFamily
from testprotocols.models.traffic import IperfProcess


@runtime_checkable
class IperfServer(Protocol):
    """Abstract contract for iperf server (traffic receiver) operations."""

    @deprecated(
        "Deprecated: use start_receiver_session. Removal not before the first release "
        "6 months after the release that deprecates it.",
        category=None,
    )
    def start_traffic_receiver(
        self,
        traffic_port: int,
        bind_to_ip: str | None = None,
        ip_version: IpFamily | int | None = None,
        udp_only: bool | None = None,
    ) -> tuple[int, str]:
        """Start an iperf traffic receiver on *traffic_port*.

        Returns the ``(pid, log_file)`` of ``start_receiver_session(...)``.

        *ip_version* is an :class:`~testprotocols.models.IpFamily` (``V4 = 4``, ``V6 = 6``) or
        ``None`` to leave the version to the tool; a plain ``int`` is the released spelling.

        Returns a tuple of (pid, log_file_path).

        Deprecated: use :meth:`start_receiver_session`. Removal not before the first release 6
        months after the release that deprecates it.
        """
        ...

    def start_receiver_session(
        self,
        traffic_port: int,
        *,
        bind_to_ip: str | None = None,
        ip_version: IpFamily | None = None,
        udp_only: bool | None = None,
    ) -> IperfProcess:
        """Start an iperf traffic receiver on *traffic_port* and return the started process
        (its pid and log file). *ip_version* is an :class:`~testprotocols.models.IpFamily` or
        ``None`` (the tool's choice); the other options mean what they mean for
        :meth:`start_traffic_receiver`."""
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
