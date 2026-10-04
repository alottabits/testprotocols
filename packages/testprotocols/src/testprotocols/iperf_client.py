"""Traffic / IperfClient template.

Defines the abstract contract for iperf client operations including
sending traffic and collecting logs.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.networking import IpFamily
from testprotocols.models.traffic import IperfProcess


@runtime_checkable
class IperfClient(Protocol):
    """Abstract contract for iperf client (traffic sender) operations."""

    def start_traffic_sender(
        self,
        host: str,
        traffic_port: int,
        bandwidth: int | None = None,
        bind_to_ip: str | None = None,
        ip_version: IpFamily | int | None = None,
        udp_protocol: bool = False,
        time: int = 10,
        client_port: int | None = None,
        udp_only: bool | None = None,
        reverse: bool = False,
        omit_s: int | None = None,
        json_output: bool = False,
        window: str | None = None,
        parallel: int | None = None,
        datagram_bytes: int | None = None,
        report_interval_s: int | None = None,
    ) -> tuple[int, str]:
        """Deprecated name of :meth:`start_sender_session`.

        Returns ``start_sender_session(...).as_tuple()``; the driver warns with
        ``warn_renamed("start_traffic_sender", "start_sender_session")`` and passes *window*
        on as ``window_bytes=parse_window_size(window)`` (``None`` stays ``None``). The
        parameters below keep their released meaning.

        Start an iperf traffic sender towards *host* on *traffic_port*.

        *ip_version* is an :class:`~testprotocols.models.IpFamily` (``V4 = 4``, ``V6 = 6``) or
        ``None`` to leave the version to the tool. An ``IpFamily`` is an ``int``, so a driver
        that formats it as ``-<ip_version>`` is unchanged; a plain ``int`` is the released
        spelling and narrows to ``IpFamily`` in a later release. A driver may convert with
        ``coerce_enum`` (a plain ``int`` is silent for an ``IntEnum``).

        Typed option parameters (each defaults to "absent": no flag emitted):

        - ``datagram_bytes``: the send buffer / datagram length (``-l <n>``).
          For UDP this fixes the on-wire datagram size — the knob a test uses
          to give concurrent streams distinct packet-size signatures that
          survive encrypted encapsulation (overhead is added, separation is
          preserved).
        - ``report_interval_s``: periodic interval reports (``-i <n>``). A
          sender log with per-interval lines is what continuity judgments
          parse (``testoperations.iperf_client.sender_life_record``); without
          it only the end-of-run summary exists.

        - ``reverse``: iperf3 reverse mode (``-R``) — the listening receiver
          transmits; the sender still initiates the connection.
        - ``parallel``: run the session over N parallel streams (``-P <n>``).
          The end-of-test ``sum``/``sum_received`` summaries aggregate across
          the streams, so a multi-stream session reports ONE aggregate rate.
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

        Returns a tuple of (pid, log_file_path).
        """
        ...

    def start_sender_session(
        self,
        host: str,
        traffic_port: int,
        *,
        bandwidth: int | None = None,
        bind_to_ip: str | None = None,
        ip_version: IpFamily | None = None,
        udp_protocol: bool = False,
        time: int = 10,
        client_port: int | None = None,
        udp_only: bool | None = None,
        reverse: bool = False,
        omit_s: int | None = None,
        json_output: bool = False,
        window_bytes: int | None = None,
        parallel: int | None = None,
        datagram_bytes: int | None = None,
        report_interval_s: int | None = None,
    ) -> IperfProcess:
        """Start an iperf traffic sender towards *host* on *traffic_port* and return the
        started process (its pid and log file).

        The options mean what they mean for :meth:`start_traffic_sender`, except:

        - ``ip_version`` is an :class:`~testprotocols.models.IpFamily` or ``None`` (the
          tool's choice);
        - ``window_bytes`` pins the socket buffer, in bytes (``-w <n>``), on both ends;
          ``None`` leaves the tool's autotuning on. It replaces the size text ``window``
          (``"8M"``; :func:`~testprotocols.models.parse_window_size` converts one).
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
