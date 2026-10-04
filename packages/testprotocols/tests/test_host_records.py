"""Host-tier record returns and the remaining ``Any`` (O8-O13, O24, O31, O32, O60-O62, M19,
M34).

Fixture data is real tool output captured on a Linux host and parsed with the parsers the
released implementers use (``jc`` for ps, syslog, ping and dig; the implementers' own regex for
``free``), so each ``as_dict()`` is checked against what a deprecated reader really returned.
"""

from __future__ import annotations

import dataclasses
import inspect
import re
import warnings
from collections.abc import Iterable, Mapping
from datetime import timedelta
from ipaddress import IPv4Address
from typing import get_type_hints

import pytest
from _helpers import protocol_attrs
from testprotocols.arp_client import ArpClient
from testprotocols.content_filtering import ContentFiltering
from testprotocols.deprecation import coerce_open_enum
from testprotocols.device_management import DeviceManagement
from testprotocols.devices import non_capability_members
from testprotocols.dhcp_server import DhcpServer
from testprotocols.dns_client import DnsClient
from testprotocols.held_prefixes import HeldPrefixes
from testprotocols.ip_routing import IpRouting
from testprotocols.models import (
    ArpEntry,
    DHCPTraceData,
    DHCPV6TraceData,
    DnsRecord,
    DnsRecordType,
    EventLogEntry,
    GroupRecord,
    MemoryUtilization,
    MulticastGroupRecordType,
    NmapPort,
    NmapPortState,
    NmapResult,
    PingResult,
    ProcessInfo,
    SyslogSeverity,
    TransportProtocol,
    UrlRules,
    group_records,
)
from testprotocols.multicast_client import MulticastClient
from testprotocols.nmap_scanner import NmapScanner
from testprotocols.ntp_client import NtpClient

# --------------------------------------------------------------------------------------
# Captured fixtures
# --------------------------------------------------------------------------------------

# ``free -b`` (procps-ng), and the released implementer's parse of the Mem: line.
FREE_B = """\
               total        used        free      shared  buff/cache   available
Mem:     33585369088  3492143104 18539642880    37384192 12067729408 30093225984
Swap:     8589930496           0  8589930496
"""


def _released_memory_parse(text: str) -> dict[str, int]:
    """The released implementer's ``get_memory_utilization`` parse, verbatim in effect."""
    keys: list[str] = []
    values: list[str] = []
    if m := re.search(r"Mem:\s+((\d+)(\s+)(\d+)(\s+)(\d+)(\s+)(\d+)(\s+)(\d+)(\s+)(\d+))", text):
        keys = ["total", "used", "free", "shared", "cache", "available"]
        values = m.group(1).strip().split()
    return dict(zip(keys, map(int, values), strict=True))


# jc ``ps`` of ``ps -A`` (the released default ``ps_options``).
PS_A_PARSED = [
    {"pid": 1, "tty": None, "time": "00:00:12", "cmd": "systemd"},
    {"pid": 2, "tty": None, "time": "00:00:00", "cmd": "kthreadd"},
]

# jc ``syslog-bsd`` of journald short lines (host name replaced) and of jc's RFC 3164 sample.
SYSLOG_PARSED = [
    {
        "priority": None,
        "date": "Oct 04 21:55:01",
        "hostname": "host1",
        "tag": "CRON",
        "content": "[3103565]: pam_unix(cron:session): session closed for user root",
    },
    {
        "priority": 34,
        "date": "Oct 11 22:14:15",
        "hostname": "mymachine",
        "tag": "su",
        "content": "'su root' failed for lonvick on /dev/pts/8",
    },
]

# jc ``dig`` answer section of a real CNAME-chain lookup (names and address replaced by
# documentation values; types, TTLs and shape as captured).
DIG_ANSWER = [
    {
        "name": "www.example.com.",
        "class": "IN",
        "type": "CNAME",
        "ttl": 3543,
        "data": "example.com.",
    },
    {"name": "example.com.", "class": "IN", "type": "A", "ttl": 3, "data": "192.0.2.4"},
]

# jc ``ping`` of ``ping -c 2 127.0.0.1`` (iputils) and of a run with every reply lost.
PING_PARSED = {
    "destination_ip": "127.0.0.1",
    "data_bytes": 56,
    "pattern": None,
    "destination": "127.0.0.1",
    "duplicates": 0,
    "packets_transmitted": 2,
    "packets_received": 2,
    "packet_loss_percent": 0.0,
    "time_ms": 1028.0,
    "round_trip_ms_min": 0.036,
    "round_trip_ms_avg": 0.041,
    "round_trip_ms_max": 0.047,
    "round_trip_ms_stddev": 0.005,
}
PING_LOST_PARSED = {
    "destination": "192.0.2.1",
    "duplicates": 0,
    "packets_transmitted": 3,
    "packets_received": 0,
    "packet_loss_percent": 100.0,
}


def _cpu_time(text: str) -> timedelta:
    days, _, clock = text.rpartition("-")
    h, m, s = (int(p) for p in clock.split(":"))
    return timedelta(days=int(days or 0), hours=h, minutes=m, seconds=s)


# --------------------------------------------------------------------------------------
# New members exist; old names stay
# --------------------------------------------------------------------------------------

NEW_MEMBERS = [
    (ContentFiltering, "read_url_rules", "get_url_rules"),
    (DeviceManagement, "read_memory_utilization", "get_memory_utilization"),
    (DeviceManagement, "read_running_processes", "get_running_processes"),
    (DeviceManagement, "read_event_log", "read_event_logs"),
    (DnsClient, "resolve", "dns_lookup"),
    (IpRouting, "ping_stats", "ping"),
    (NmapScanner, "scan", "nmap"),
    (ArpClient, "read_arp_table", "get_arp_table"),
    (NtpClient, "read_date", "get_date"),
]


@pytest.mark.parametrize(("protocol", "new", "old"), NEW_MEMBERS)
def test_new_member_and_old_name_are_protocol_members(protocol: type, new: str, old: str) -> None:
    attrs = protocol_attrs(protocol)
    assert new in attrs
    assert old in attrs


@pytest.mark.parametrize(
    ("protocol", "member", "returns"),
    [
        (ContentFiltering, "read_url_rules", "UrlRules"),
        (DeviceManagement, "read_memory_utilization", "MemoryUtilization"),
        (DeviceManagement, "read_running_processes", "list[ProcessInfo]"),
        (DeviceManagement, "read_event_log", "list[EventLogEntry]"),
        (DnsClient, "resolve", "list[DnsRecord]"),
        (IpRouting, "ping_stats", "PingResult"),
        (NmapScanner, "scan", "NmapResult"),
        (ArpClient, "read_arp_table", "list[ArpEntry]"),
        (NtpClient, "read_date", "datetime | None"),
    ],
)
def test_new_member_returns_the_record(protocol: type, member: str, returns: str) -> None:
    assert inspect.signature(getattr(protocol, member)).return_annotation == returns


@pytest.mark.parametrize(("protocol", "new", "old"), NEW_MEMBERS)
def test_old_name_is_documented_deprecated(protocol: type, new: str, old: str) -> None:
    doc = inspect.getdoc(getattr(protocol, old)) or ""
    assert "deprecated" in doc.lower() and new in doc


def test_new_members_take_no_tool_option_string() -> None:
    for protocol, member in [
        (DeviceManagement, "read_running_processes"),
        (DnsClient, "resolve"),
        (IpRouting, "ping_stats"),
        (NmapScanner, "scan"),
    ]:
        params = inspect.signature(getattr(protocol, member)).parameters
        assert not {"options", "opts", "ps_options"} & set(params), member


# --------------------------------------------------------------------------------------
# O8 UrlRules
# --------------------------------------------------------------------------------------


def test_url_rules_as_tuple_is_the_released_return() -> None:
    rules = UrlRules(allowed=("*.example.com",), blocked=("bad.example.net", "*.test"))
    assert rules.as_tuple() == (["*.example.com"], ["bad.example.net", "*.test"])
    assert UrlRules().as_tuple() == ([], [])


def test_old_reader_matches_new_record_url_rules() -> None:
    # the released implementer returns (list(allowed patterns), list(blocked patterns))
    released = (["*.example.com"], ["bad.example.net"])
    assert UrlRules(tuple(released[0]), tuple(released[1])).as_tuple() == released


def test_url_rules_takes_a_list_and_holds_a_tuple() -> None:
    rules = UrlRules(allowed=["a.example"], blocked=[])  # type: ignore[arg-type]
    assert rules.allowed == ("a.example",)


@pytest.mark.parametrize(
    "kwargs",
    [{"allowed": "a.example"}, {"blocked": [1]}, {"allowed": None}],
)
def test_url_rules_refuses_wrong_types(kwargs: dict[str, object]) -> None:
    with pytest.raises(TypeError):
        UrlRules(**kwargs)  # type: ignore[arg-type]


# --------------------------------------------------------------------------------------
# O9 MemoryUtilization
# --------------------------------------------------------------------------------------


def test_old_reader_matches_new_record_memory() -> None:
    released = _released_memory_parse(FREE_B)
    record = MemoryUtilization(
        total_bytes=released["total"],
        used_bytes=released["used"],
        free_bytes=released["free"],
        shared_bytes=released["shared"],
        cache_bytes=released["cache"],
        available_bytes=released["available"],
    )
    assert record.as_dict() == released
    assert list(record.as_dict()) == list(released)  # same key order


def test_memory_optional_figures_are_left_out_of_the_dict() -> None:
    record = MemoryUtilization(total_bytes=10, used_bytes=4, free_bytes=6)
    assert record.as_dict() == {"total": 10, "used": 4, "free": 6}


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"total_bytes": -1, "used_bytes": 0, "free_bytes": 0}, ValueError),
        ({"total_bytes": "10", "used_bytes": 0, "free_bytes": 0}, TypeError),
        ({"total_bytes": 10, "used_bytes": True, "free_bytes": 0}, TypeError),
        ({"total_bytes": 10, "used_bytes": 0, "free_bytes": 0, "cache_bytes": 1.5}, TypeError),
    ],
)
def test_memory_refuses_bad_values(kwargs: dict[str, object], error: type[Exception]) -> None:
    with pytest.raises(error):
        MemoryUtilization(**kwargs)  # type: ignore[arg-type]


# --------------------------------------------------------------------------------------
# O10 ProcessInfo
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("entry", PS_A_PARSED)
def test_old_reader_matches_new_record_process(entry: dict[str, object]) -> None:
    record = ProcessInfo(
        pid=entry["pid"],  # type: ignore[arg-type]
        tty=entry["tty"],  # type: ignore[arg-type]
        cpu_time=_cpu_time(entry["time"]),  # type: ignore[arg-type]
        command=entry["cmd"],  # type: ignore[arg-type]
    )
    assert record.as_dict() == entry


def test_process_cpu_time_beyond_a_day_uses_the_ps_day_prefix() -> None:
    # procps TIME is [DD-]hh:mm:ss
    record = ProcessInfo(pid=7, tty="pts/0", cpu_time=timedelta(days=1, seconds=7384), command="x")
    assert record.as_dict()["time"] == "1-02:03:04"
    assert _cpu_time("1-02:03:04") == record.cpu_time


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"pid": -1}, ValueError),
        ({"pid": "1"}, TypeError),
        ({"cpu_time": timedelta(seconds=-1)}, ValueError),
        ({"cpu_time": timedelta(milliseconds=1500)}, ValueError),
        ({"cpu_time": "00:00:01"}, TypeError),
        ({"tty": 0}, TypeError),
        ({"command": None}, TypeError),
    ],
)
def test_process_refuses_bad_values(kwargs: dict[str, object], error: type[Exception]) -> None:
    base: dict[str, object] = {"pid": 1, "tty": None, "cpu_time": timedelta(0), "command": "init"}
    with pytest.raises(error):
        ProcessInfo(**(base | kwargs))  # type: ignore[arg-type]


# --------------------------------------------------------------------------------------
# O11 EventLogEntry
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("entry", SYSLOG_PARSED)
def test_old_reader_matches_new_record_event_log(entry: dict[str, object]) -> None:
    record = EventLogEntry(
        timestamp=entry["date"],  # type: ignore[arg-type]
        hostname=entry["hostname"],  # type: ignore[arg-type]
        tag=entry["tag"],  # type: ignore[arg-type]
        message=entry["content"],  # type: ignore[arg-type]
        priority=entry["priority"],  # type: ignore[arg-type]
    )
    assert record.as_dict() == entry


def test_event_log_severity_is_the_priority_low_bits() -> None:
    entry = EventLogEntry("Oct 11 22:14:15", "mymachine", "su", "x", priority=34)
    assert entry.severity is SyslogSeverity.CRITICAL  # 34 = facility 4 (auth) * 8 + 2
    assert EventLogEntry("Oct 11 22:14:15", "h", None, "x").severity is None
    assert [m.value for m in SyslogSeverity] == list(range(8))


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"priority": 192}, ValueError),
        ({"priority": -1}, ValueError),
        ({"priority": "34"}, TypeError),
        ({"timestamp": None}, TypeError),
        ({"tag": 5}, TypeError),
        ({"message": b"x"}, TypeError),
    ],
)
def test_event_log_refuses_bad_values(kwargs: dict[str, object], error: type[Exception]) -> None:
    base: dict[str, object] = {
        "timestamp": "Oct 04 21:55:01",
        "hostname": "h",
        "tag": "t",
        "message": "m",
    }
    with pytest.raises(error):
        EventLogEntry(**(base | kwargs))  # type: ignore[arg-type]


# --------------------------------------------------------------------------------------
# O13 DnsRecord
# --------------------------------------------------------------------------------------


def _record_from_answer(entry: Mapping[str, object]) -> DnsRecord:
    word = entry["type"]
    assert isinstance(word, str)
    try:
        record_type, raw = DnsRecordType(word), None
    except ValueError:
        record_type, raw = DnsRecordType.OTHER, word
    return DnsRecord(
        name=entry["name"],  # type: ignore[arg-type]
        record_type=record_type,
        ttl=entry["ttl"],  # type: ignore[arg-type]
        data=entry["data"],  # type: ignore[arg-type]
        record_type_raw=raw,
    )


def test_dns_records_from_a_real_answer_section() -> None:
    records = [_record_from_answer(e) for e in DIG_ANSWER]
    assert [r.record_type for r in records] == [DnsRecordType.CNAME, DnsRecordType.A]
    assert records[1].data == "192.0.2.4" and records[1].ttl == 3
    assert records[0].name == "www.example.com."


def test_dns_record_type_outside_the_enum_is_other_with_the_raw_word() -> None:
    record = _record_from_answer(
        {"name": "example.com.", "class": "IN", "type": "CAA", "ttl": 60, "data": '0 issue "ca"'}
    )
    assert record.record_type is DnsRecordType.OTHER
    assert record.record_type_raw == "CAA"
    with pytest.raises(ValueError):
        DnsRecord("a.", DnsRecordType.A, 1, "192.0.2.1", record_type_raw="A6")


def test_dns_record_plain_word_naming_a_member_warns() -> None:
    with pytest.warns(DeprecationWarning, match="DnsRecordType.A"):
        record = DnsRecord("a.", "A", 1, "192.0.2.1")  # type: ignore[arg-type]
    assert record.record_type is DnsRecordType.A


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"ttl": -1}, ValueError),
        ({"ttl": "60"}, TypeError),
        ({"name": None}, TypeError),
        ({"data": 1}, TypeError),
    ],
)
def test_dns_record_refuses_bad_values(kwargs: dict[str, object], error: type[Exception]) -> None:
    base: dict[str, object] = {
        "name": "a.",
        "record_type": DnsRecordType.A,
        "ttl": 1,
        "data": "192.0.2.1",
    }
    with pytest.raises(error):
        DnsRecord(**(base | kwargs))  # type: ignore[arg-type]


def test_dns_record_type_other_is_open_set_helper_compatible() -> None:
    assert coerce_open_enum(DnsRecordType, "CAA", what="x", other=DnsRecordType.OTHER) == (
        DnsRecordType.OTHER,
        "CAA",
    )


def test_resolve_takes_the_enum() -> None:
    params = inspect.signature(DnsClient.resolve).parameters
    assert params["record_type"].annotation == "DnsRecordType"


# --------------------------------------------------------------------------------------
# O24 PingResult
# --------------------------------------------------------------------------------------


def _ping_from_parsed(parsed: Mapping[str, object]) -> PingResult:
    return PingResult(
        destination=parsed["destination"],  # type: ignore[arg-type]
        transmitted=parsed["packets_transmitted"],  # type: ignore[arg-type]
        received=parsed["packets_received"],  # type: ignore[arg-type]
        duplicates=parsed["duplicates"],  # type: ignore[arg-type]
        packet_loss_percent=parsed["packet_loss_percent"],  # type: ignore[arg-type]
        rtt_min_ms=parsed.get("round_trip_ms_min"),  # type: ignore[arg-type]
        rtt_avg_ms=parsed.get("round_trip_ms_avg"),  # type: ignore[arg-type]
        rtt_max_ms=parsed.get("round_trip_ms_max"),  # type: ignore[arg-type]
        rtt_stddev_ms=parsed.get("round_trip_ms_stddev"),  # type: ignore[arg-type]
    )


def test_ping_result_from_real_output() -> None:
    result = _ping_from_parsed(PING_PARSED)
    assert (result.transmitted, result.received, result.packet_loss_percent) == (2, 2, 0.0)
    assert result.rtt_avg_ms == 0.041
    lost = _ping_from_parsed(PING_LOST_PARSED)
    assert lost.received == 0 and lost.rtt_min_ms is None and lost.packet_loss_percent == 100.0


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"transmitted": -1}, ValueError),
        ({"received": "2"}, TypeError),
        ({"packet_loss_percent": 100.5}, ValueError),
        ({"packet_loss_percent": True}, TypeError),
        ({"rtt_avg_ms": -0.1}, ValueError),
        ({"destination": None}, TypeError),
    ],
)
def test_ping_result_refuses_bad_values(kwargs: dict[str, object], error: type[Exception]) -> None:
    base: dict[str, object] = {
        "destination": "127.0.0.1",
        "transmitted": 2,
        "received": 2,
        "packet_loss_percent": 0.0,
    }
    with pytest.raises(error):
        PingResult(**(base | kwargs))  # type: ignore[arg-type]


def test_ping_json_output_is_documented_deprecated() -> None:
    doc = inspect.getdoc(IpRouting.ping) or ""
    assert "json_output" in doc and "ping_stats" in doc and "eprecated" in doc


# --------------------------------------------------------------------------------------
# O31 NmapResult
# --------------------------------------------------------------------------------------


def test_nmap_result_from_the_released_normalised_shape() -> None:
    # the private implementer's normalised dict for its unit-test XML: port numbers 22 and
    # 80, states "open" and "closed", service "ssh" and none
    released_ports: list[tuple[int, str, str, str | None]] = [
        (22, "tcp", "open", "ssh"),
        (80, "tcp", "closed", None),
    ]
    result = NmapResult(
        up=True,
        addresses=("192.168.114.9",),
        ports=(
            NmapPort(22, TransportProtocol.TCP, NmapPortState.OPEN, "ssh"),
            NmapPort(80, TransportProtocol.TCP, NmapPortState.CLOSED, None),
        ),
    )
    assert [
        (p.port, str(p.protocol), str(p.state), p.service) for p in result.ports
    ] == released_ports


def test_nmap_port_states_are_nmaps_six() -> None:
    assert [s.value for s in NmapPortState] == [
        "open",
        "closed",
        "filtered",
        "unfiltered",
        "open|filtered",
        "closed|filtered",
    ]


@pytest.mark.parametrize(
    "build",
    [
        lambda: NmapPort(0, TransportProtocol.TCP, NmapPortState.OPEN, None),
        lambda: NmapPort(65536, TransportProtocol.TCP, NmapPortState.OPEN, None),
    ],
)
def test_nmap_port_refuses_out_of_range(build) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError):
        build()


@pytest.mark.parametrize(
    "build",
    [
        lambda: NmapPort("22", TransportProtocol.TCP, NmapPortState.OPEN, None),  # type: ignore[arg-type]
        lambda: NmapPort(22, TransportProtocol.TCP, NmapPortState.OPEN, 1),  # type: ignore[arg-type]
        lambda: NmapResult(up=1, addresses=(), ports=()),  # type: ignore[arg-type]
        lambda: NmapResult(up=True, addresses="10.0.0.1", ports=()),  # type: ignore[arg-type]
        lambda: NmapResult(up=True, addresses=(), ports=({"port": 22},)),  # type: ignore[arg-type]
    ],
)
def test_nmap_records_refuse_wrong_types(build) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(TypeError):
        build()


def test_nmap_port_takes_released_words_with_a_warning() -> None:
    with pytest.warns(DeprecationWarning):
        port = NmapPort(22, "tcp", "open", "ssh")  # type: ignore[arg-type]
    assert port.protocol is TransportProtocol.TCP and port.state is NmapPortState.OPEN
    with pytest.raises(ValueError):
        NmapPort(22, TransportProtocol.TCP, "half-open", None)  # type: ignore[arg-type]


def test_scan_signature() -> None:
    params = inspect.signature(NmapScanner.scan).parameters
    assert params["ip_version"].annotation == "IpVersion"
    assert params["ports"].annotation == "Sequence[PortRange]"
    assert params["protocol"].annotation == "TransportProtocol | None"


# --------------------------------------------------------------------------------------
# O62 ArpEntry
# --------------------------------------------------------------------------------------

# ``arp -n`` (net-tools) and the released use case's parse of it.
ARP_N = """\
Address                  HWtype  HWaddress           Flags Mask            Iface
192.168.1.1              ether   aa:bb:cc:00:11:22   C                     eth0
"""


def test_arp_entry_from_a_real_table_line() -> None:
    m = re.search(
        r"(?P<address>\d+.\d+.\d+.\d+)\s+(?P<hw_type>\S+)\s+"
        r"(?P<hw_address>\S+)\s+(?P<flags_mask>\S+)\s+(?P<iface>\S+)",
        ARP_N.splitlines()[1],
    )
    assert m is not None
    row = m.groupdict()
    entry = ArpEntry(
        address=IPv4Address(row["address"]),
        hw_type=row["hw_type"],
        hw_address=row["hw_address"],
        flags=row["flags_mask"],
        interface=row["iface"],
    )
    assert entry.address == IPv4Address("192.168.1.1") and entry.interface == "eth0"


@pytest.mark.parametrize(
    "kwargs",
    [{"address": "192.168.1.1"}, {"hw_address": None}, {"interface": 0}, {"flags": None}],
)
def test_arp_entry_refuses_wrong_types(kwargs: dict[str, object]) -> None:
    base: dict[str, object] = {
        "address": IPv4Address("192.0.2.1"),
        "hw_type": "ether",
        "hw_address": "aa:bb:cc:00:11:22",
        "flags": "C",
        "interface": "eth0",
    }
    with pytest.raises(TypeError):
        ArpEntry(**(base | kwargs))  # type: ignore[arg-type]


# --------------------------------------------------------------------------------------
# O60 GroupRecord
# --------------------------------------------------------------------------------------


def _released_mld_args(
    records: Iterable[tuple[list[str], str, MulticastGroupRecordType]],
) -> str:
    """The released implementers' rendering (palco and boardfarm ``_send_multicast_report``)."""
    args = ""
    for sources, group, rtype in records:
        src = ",".join(sources)
        args += f'-mr "{src};{group};{rtype.value} "'
    return args


def test_group_record_renders_as_the_released_tuple() -> None:
    rtype = MulticastGroupRecordType.MODE_IS_INCLUDE
    record = GroupRecord(["2001:db8::1", "2001:db8::2"], "ff3e::1234", rtype)
    released = (["2001:db8::1", "2001:db8::2"], "ff3e::1234", rtype)
    assert record == released
    assert _released_mld_args([record]) == _released_mld_args([released])
    assert (record.sources, record.group, record.record_type) == released


def test_group_record_fits_the_released_parameter_type() -> None:
    hints = get_type_hints(MulticastClient.send_mldv2_report)
    assert "list[tuple[list[str], str, " in str(hints["mcast_group_record"])
    assert issubclass(GroupRecord, tuple)


def test_group_records_converts_a_plain_tuple_with_a_warning() -> None:
    rtype = MulticastGroupRecordType.ALLOW_NEW_SOURCES
    record = GroupRecord([], "ff3e::1", rtype)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert group_records([record], what="records") == [record]
    with pytest.warns(DeprecationWarning, match="GroupRecord"):
        converted = group_records([([], "ff3e::1", rtype)], what="records")
    assert converted == [record] and isinstance(converted[0], GroupRecord)


@pytest.mark.parametrize(
    "build",
    [
        lambda: GroupRecord("2001:db8::1", "ff3e::1", MulticastGroupRecordType.MODE_IS_INCLUDE),  # type: ignore[arg-type]
        lambda: GroupRecord([1], "ff3e::1", MulticastGroupRecordType.MODE_IS_INCLUDE),  # type: ignore[list-item]
        lambda: GroupRecord([], None, MulticastGroupRecordType.MODE_IS_INCLUDE),  # type: ignore[arg-type]
        lambda: GroupRecord([], "ff3e::1", 1),  # type: ignore[arg-type]
    ],
)
def test_group_record_refuses_wrong_types(build) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(TypeError):
        build()


def test_group_records_refuses_a_wrong_shape() -> None:
    with pytest.raises(TypeError):
        group_records([("ff3e::1",)], what="records")  # type: ignore[list-item]


# --------------------------------------------------------------------------------------
# O12, O32, O61, M19, M34 and the remaining Any
# --------------------------------------------------------------------------------------


def test_provision_cpe_options_are_pool_to_option_maps() -> None:
    params = inspect.signature(DhcpServer.provision_cpe).parameters
    for name in ("dhcpv4_options", "dhcpv6_options"):
        assert params[name].annotation == "dict[str, dict[str, object]]"


def test_hold_stays_str_for_released_implementers() -> None:
    params = inspect.signature(HeldPrefixes.hold).parameters
    assert params["address"].annotation == "str"
    assert "IPv4Interface" in (inspect.getdoc(HeldPrefixes.hold) or "")


def test_dhcp_trace_packets_are_read_only_mappings() -> None:
    for model, name in ((DHCPTraceData, "dhcp_packet"), (DHCPV6TraceData, "dhcpv6_packet")):
        hint = {f.name: f.type for f in dataclasses.fields(model)}[name]
        assert hint == "Mapping[str, object]"


def test_non_capability_members_still_reads_protocol_attrs() -> None:
    from typing import Protocol

    class _Sample(Protocol):
        device_name: str
        flag: bool

    assert non_capability_members(_Sample) == frozenset({"flag"})


def test_read_date_documents_naive_local_time() -> None:
    doc = inspect.getdoc(NtpClient.read_date) or ""
    assert "naive" in doc
