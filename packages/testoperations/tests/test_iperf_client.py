"""Tests for testoperations.iperf_client module."""

from __future__ import annotations

import inspect
import warnings
from collections.abc import Callable
from unittest.mock import MagicMock

import pytest
from testoperations.iperf_client import IperfSession, sender_life_record, start_iperf
from testprotocols.models import IperfProcess, IpFamily

# ---------------------------------------------------------------------------
# start_iperf
# ---------------------------------------------------------------------------

CLIENT_OLD = ["start_traffic_sender", "stop_traffic", "get_iperf_logs"]
CLIENT_NEW = [*CLIENT_OLD, "start_sender_session"]
SERVER_OLD = ["start_traffic_receiver", "stop_traffic", "get_iperf_logs"]
SERVER_NEW = [*SERVER_OLD, "start_receiver_session"]


def _pair(new: bool) -> tuple[MagicMock, MagicMock]:
    client = MagicMock(spec=CLIENT_NEW if new else CLIENT_OLD)
    server = MagicMock(spec=SERVER_NEW if new else SERVER_OLD)
    if new:
        client.start_sender_session.return_value = IperfProcess(41, "log_s.txt")
        server.start_receiver_session.return_value = IperfProcess(42, "log_r.txt")
    else:
        client.start_traffic_sender.return_value = (41, "log_s.txt")
        server.start_traffic_receiver.return_value = (42, "log_r.txt")
    return client, server


@pytest.mark.parametrize("new", [False, True])
class TestStartIperf:
    def test_returns_the_session_record(self, new: bool) -> None:
        client, server = _pair(new)
        session = start_iperf(client, server, port=5001, host="192.0.2.9")
        assert session == IperfSession(
            sender=IperfProcess(41, "log_s.txt"), receiver=IperfProcess(42, "log_r.txt")
        )
        assert session.sender.pid == 41 and session.receiver.log_file == "log_r.txt"

    def test_calls_protocol_members_receiver_first(self, new: bool) -> None:
        client, server = _pair(new)
        order: list[str] = []
        start_c = client.start_sender_session if new else client.start_traffic_sender
        start_s = server.start_receiver_session if new else server.start_traffic_receiver

        def _started(label: str, pid: int, log: str) -> Callable[..., object]:
            def _start(*_a: object, **_k: object) -> object:
                order.append(label)
                return IperfProcess(pid, log) if new else (pid, log)

            return _start

        start_s.side_effect = _started("receiver", 42, "log_r.txt")
        start_c.side_effect = _started("sender", 41, "log_s.txt")
        start_iperf(client, server, port=5001, host="192.0.2.9")
        assert order == ["receiver", "sender"]

    def test_passes_port_host_and_options(self, new: bool) -> None:
        client, server = _pair(new)
        start_iperf(client, server, port=5201, time=30, udp=True, ip_version=6, host="h")
        start_c = client.start_sender_session if new else client.start_traffic_sender
        start_s = server.start_receiver_session if new else server.start_traffic_receiver
        start_c.assert_called_once_with(
            "h", 5201, time=30, udp_protocol=True, ip_version=IpFamily.V6
        )
        start_s.assert_called_once_with(5201, ip_version=IpFamily.V6, udp_only=True)

    def test_a_number_ip_version_is_silent_and_a_bad_one_raises(self, new: bool) -> None:
        client, server = _pair(new)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            start_iperf(client, server, port=5001, ip_version=IpFamily.V4, host="h")
            start_iperf(client, server, port=5001, ip_version=4, host="h")
        with pytest.raises(ValueError, match="ip_version"):
            start_iperf(client, server, port=5001, ip_version=5, host="h")

    def test_the_released_default_is_4_and_does_not_warn(self, new: bool) -> None:
        default = inspect.signature(start_iperf).parameters["ip_version"].default
        assert default == 4 and type(default) is int  # the released default
        client, server = _pair(new)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            start_iperf(client, server, port=5001, host="h")
        start_s = server.start_receiver_session if new else server.start_traffic_receiver
        assert start_s.call_args.kwargs["ip_version"] is IpFamily.V4

    def test_an_explicit_plain_4_is_the_member_without_a_warning(self, new: bool) -> None:
        # an IntEnum's value is the number, not a deprecated spelling: no warning by design
        client, server = _pair(new)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            start_iperf(client, server, port=5001, ip_version=4, host="h")
        start_s = server.start_receiver_session if new else server.start_traffic_receiver
        assert start_s.call_args.kwargs["ip_version"] is IpFamily.V4

    def test_host_is_required_keyword_only(self, new: bool) -> None:
        client, server = _pair(new)
        with pytest.raises(TypeError, match="host"):
            start_iperf(client, server, 5001)  # type: ignore[call-arg]


class TestReleasedReadAccess:
    """The released ``dict`` keys read through the record, with a DeprecationWarning."""

    def _session(self) -> IperfSession:
        client, server = _pair(True)
        return start_iperf(client, server, port=5001, host="h")

    def test_indexing_warns_and_returns_the_released_values(self) -> None:
        session = self._session()
        with pytest.warns(DeprecationWarning, match="indexing"):
            assert session["sender_pid"] == 41
        with pytest.warns(DeprecationWarning):
            assert session["sender_log"] == "log_s.txt"
            assert session["receiver_pid"] == 42
            assert session["receiver_log"] == "log_r.txt"

    def test_as_dict_equals_the_released_dict(self) -> None:
        with pytest.warns(DeprecationWarning, match="as_dict"):
            released = self._session().as_dict()
        assert released == {
            "sender_pid": 41,
            "sender_log": "log_s.txt",
            "receiver_pid": 42,
            "receiver_log": "log_r.txt",
        }

    def test_dict_conversion_and_unpacking_still_work(self) -> None:
        session = self._session()
        with pytest.warns(DeprecationWarning):
            assert dict(session)["sender_pid"] == 41
            assert {**session}["receiver_pid"] == 42

    def test_get_in_and_equality_with_the_released_dict(self) -> None:
        session = self._session()
        with pytest.warns(DeprecationWarning):
            assert session.get("sender_pid") == 41
            assert "sender_log" in session
            assert session == {
                "sender_pid": 41,
                "sender_log": "log_s.txt",
                "receiver_pid": 42,
                "receiver_log": "log_r.txt",
            }

    def test_unknown_key_raises_keyerror(self) -> None:
        with pytest.warns(DeprecationWarning), pytest.raises(KeyError):
            self._session()["nope"]

    def test_reading_the_fields_never_warns(self) -> None:
        session = self._session()
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            assert session.sender.pid == 41
            assert session == self._session()
            assert hash(session) == hash(self._session())


# ---------------------------------------------------------------------------
# sender_life_record
# ---------------------------------------------------------------------------

IPERF3_LOG = """\
Connecting to host 198.51.100.9, port 5201
[  5] local 10.1.30.50 port 47000 connected to 198.51.100.9 port 5201
[ ID] Interval           Transfer     Bitrate
[  5]   0.00-1.00   sec  1.25 MBytes  10.5 Mbits/sec
[  5]   1.00-2.00   sec  1.25 MBytes  10.5 Mbits/sec
[  5]   2.00-3.00   sec  1.25 MBytes  10.5 Mbits/sec
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate
[  5]   0.00-3.00   sec  3.75 MBytes  10.5 Mbits/sec                  sender
"""

IPERF2_GAPPY_LOG = """\
[  3] local 10.1.30.51 port 51000 connected with 198.51.100.4 port 5001
[ ID] Interval       Transfer     Bandwidth
[  3]  0.0- 1.0 sec  128 KBytes  1.05 Mbits/sec
[  3]  1.0- 2.0 sec  128 KBytes  1.05 Mbits/sec
[  3]  4.0- 5.0 sec  128 KBytes  1.05 Mbits/sec
[  3]  0.0- 5.0 sec  384 KBytes  0.63 Mbits/sec
"""


class TestSenderLifeRecord:
    def test_counts_intervals_and_excludes_summary(self) -> None:
        client = MagicMock()
        client.get_iperf_logs.return_value = IPERF3_LOG

        record = sender_life_record(client, "sender.log")

        client.get_iperf_logs.assert_called_once_with("sender.log")
        assert record.intervals == 3
        assert record.gaps == ()
        assert record.total_bytes == 3 * int(1.25 * 1024**2)

    def test_detects_gap_between_intervals(self) -> None:
        client = MagicMock()
        client.get_iperf_logs.return_value = IPERF2_GAPPY_LOG

        record = sender_life_record(client, "sender.log")

        assert record.intervals == 3
        assert record.gaps == ((2.0, 4.0),)

    def test_no_interval_lines_is_no_recorded_life(self) -> None:
        client = MagicMock()
        client.get_iperf_logs.return_value = "connect failed: No route to host\n"

        record = sender_life_record(client, "sender.log")

        assert record.intervals == 0
        assert record.gaps == ()
        assert record.total_bytes == 0

    def test_gap_tolerance_suppresses_small_holes(self) -> None:
        client = MagicMock()
        client.get_iperf_logs.return_value = IPERF2_GAPPY_LOG

        record = sender_life_record(client, "sender.log", gap_tolerance_s=2.5)

        assert record.gaps == ()
