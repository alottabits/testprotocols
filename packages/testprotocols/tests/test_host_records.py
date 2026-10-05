"""Host-tier record returns and the remaining ``Any``.

Fixture data is real tool output captured on a Linux host and parsed with the parsers the
released implementers use (``jc`` for ps, syslog, ping and dig; the implementers' own regex for
``free``), so each record's fields are checked against what a deprecated reader really
returned.
"""

from __future__ import annotations

import dataclasses
import inspect
import re
from collections.abc import Iterable, Mapping
from datetime import timedelta
from ipaddress import IPv4Address
from typing import get_type_hints

import pytest
from _helpers import protocol_attrs
from testprotocols.arp_client import ArpClient
from testprotocols.content_filtering import ContentFiltering
from testprotocols.device_management import DeviceManagement
from testprotocols.devices import non_capability_members
from testprotocols.dhcp_server import DhcpServer
from testprotocols.dns_client import DnsClient
from testprotocols.held_prefixes import HeldPrefixes
from testprotocols.ip_routing import IpRouting
from testprotocols.iperf_client import IperfClient
from testprotocols.iperf_server import IperfServer
from testprotocols.models import (
    ArpEntry,
    Blackout,
    Brownout,
    DHCPTraceData,
    DHCPV6TraceData,
    DnsRecord,
    EventLogEntry,
    GroupRecord,
    IperfProcess,
    LatencySpike,
    MemoryUtilization,
    MulticastGroupRecordType,
    NmapPort,
    NmapPortState,
    NmapResult,
    PacketStorm,
    PingResult,
    ProcessInfo,
    SyslogSeverity,
    TransientEvent,
    TransportProtocol,
    UrlRules,
)
from testprotocols.multicast_client import MulticastClient
from testprotocols.netem_controller import NetemController
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
    (DeviceManagement, "read_log_entries", "read_event_logs"),
    (DnsClient, "resolve", "dns_lookup"),
    (IperfClient, "start_sender_session", "start_traffic_sender"),
    (IperfServer, "start_receiver_session", "start_traffic_receiver"),
    (IpRouting, "ping_stats", "ping"),
    (NmapScanner, "scan_ports", "nmap"),
    (ArpClient, "read_arp_table", "get_arp_table"),
    (NtpClient, "read_date", "get_date"),
    (NetemController, "inject_event", "inject_transient"),
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
        (DeviceManagement, "read_log_entries", "list[EventLogEntry]"),
        (DnsClient, "resolve", "list[DnsRecord]"),
        (IperfClient, "start_sender_session", "IperfProcess"),
        (IperfServer, "start_receiver_session", "IperfProcess"),
        (IpRouting, "ping_stats", "PingResult"),
        (NmapScanner, "scan_ports", "NmapResult"),
        (ArpClient, "read_arp_table", "list[ArpEntry]"),
        (NtpClient, "read_date", "datetime | None"),
        (NetemController, "inject_event", "None"),
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
        (NmapScanner, "scan_ports"),
    ]:
        params = inspect.signature(getattr(protocol, member)).parameters
        assert not {"options", "opts", "ps_options"} & set(params), member


# --------------------------------------------------------------------------------------
# UrlRules
# --------------------------------------------------------------------------------------


def _released_url_rules(settings: dict[str, list[str]]) -> tuple[list[str], list[str]]:
    """A released reader's shape: the appliance's two pattern lists, copied into lists."""
    return list(settings.get("allowed", [])), list(settings.get("blocked", []))


def test_old_reader_matches_new_record_url_rules() -> None:
    settings = {"allowed": ["*.example.com"], "blocked": ["bad.example.net", "*.test"]}
    released = _released_url_rules(settings)
    # a driver builds the record from the same device settings, not from the released tuple
    record = UrlRules(allowed=tuple(settings["allowed"]), blocked=tuple(settings["blocked"]))
    assert (list(record.allowed), list(record.blocked)) == released
    assert UrlRules() == UrlRules(allowed=(), blocked=())


# --------------------------------------------------------------------------------------
# MemoryUtilization
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
    held = {
        "total": record.total_bytes,
        "used": record.used_bytes,
        "free": record.free_bytes,
        "shared": record.shared_bytes,
        "cache": record.cache_bytes,
        "available": record.available_bytes,
    }
    assert held == released


# --------------------------------------------------------------------------------------
# ProcessInfo
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("entry", PS_A_PARSED)
def test_old_reader_matches_new_record_process(entry: dict[str, object]) -> None:
    record = ProcessInfo(
        pid=entry["pid"],  # type: ignore[arg-type]
        tty=entry["tty"],  # type: ignore[arg-type]
        cpu_time=_cpu_time(entry["time"]),  # type: ignore[arg-type]
        command=entry["cmd"],  # type: ignore[arg-type]
    )
    assert (record.pid, record.tty, record.command) == (entry["pid"], entry["tty"], entry["cmd"])


def test_process_cpu_time_beyond_a_day_uses_the_ps_day_prefix() -> None:
    # procps TIME is [DD-]hh:mm:ss
    assert _cpu_time("1-02:03:04") == timedelta(days=1, seconds=7384)


# --------------------------------------------------------------------------------------
# EventLogEntry
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
    held = {
        "priority": record.priority,
        "date": record.timestamp,
        "hostname": record.hostname,
        "tag": record.tag,
        "content": record.message,
    }
    assert held == entry


def test_event_log_reader_keeps_unparsable_lines_in_the_released_output() -> None:
    # jc syslog-bsd emits {"unparsable": line} for a line it cannot read; no record holds it,
    # so the deprecated reader is documented as keeping its released output
    doc = inspect.getdoc(DeviceManagement.read_event_logs) or ""  # type: ignore[deprecated]
    assert "unparsable" in doc and "released output also carries" in doc
    assert "left out" in (inspect.getdoc(DeviceManagement.read_log_entries) or "")


def test_event_log_severity_is_the_priority_low_bits() -> None:
    entry = EventLogEntry("Oct 11 22:14:15", "mymachine", "su", "x", priority=34)
    assert entry.severity is SyslogSeverity.CRITICAL  # 34 = facility 4 (auth) * 8 + 2
    assert EventLogEntry("Oct 11 22:14:15", "h", None, "x").severity is None
    assert [m.value for m in SyslogSeverity] == list(range(8))


# --------------------------------------------------------------------------------------
# DnsRecord
# --------------------------------------------------------------------------------------


def _record_from_answer(entry: Mapping[str, object]) -> DnsRecord:
    return DnsRecord(
        name=entry["name"],  # type: ignore[arg-type]
        record_type=entry["type"],  # type: ignore[arg-type]
        ttl=entry["ttl"],  # type: ignore[arg-type]
        data=entry["data"],  # type: ignore[arg-type]
    )


def test_dns_records_from_a_real_answer_section() -> None:
    records = [_record_from_answer(e) for e in DIG_ANSWER]
    assert [r.record_type for r in records] == ["CNAME", "A"]
    assert records[1].data == "192.0.2.4" and records[1].ttl == 3
    assert records[0].name == "www.example.com."


def test_dns_record_type_outside_the_enum_is_stored_as_given() -> None:
    record = _record_from_answer(
        {"name": "example.com.", "class": "IN", "type": "CAA", "ttl": 60, "data": '0 issue "ca"'}
    )
    assert record.record_type == "CAA"


def test_record_type_parameters_take_the_enum_or_its_text() -> None:
    for member in (DnsClient.dns_lookup, DnsClient.resolve):  # type: ignore[deprecated]
        params = inspect.signature(member).parameters
        assert params["record_type"].annotation == "DnsRecordType | str"


# --------------------------------------------------------------------------------------
# IperfProcess and the window size
# --------------------------------------------------------------------------------------


# A ``ps auxwwww`` line for a started iperf3 receiver (procps), as the released host
# implementer reads the pid from it, and that implementer's log path.
PS_IPERF_LINE = (
    "root        4242  0.0  0.0  10364  3712 ?        S    21:50   0:00 iperf3 -s -p 5201"
)
IPERF_LOG = "/tmp/iperf_server_logs.txt"


def _released_receiver_return(ps_line: str, log_file: str) -> tuple[int, str]:
    """The released implementer's return: ``int(line.split()[1]), log_file_path``."""
    return int(ps_line.split()[1]), log_file


def test_old_reader_matches_new_record_iperf() -> None:
    released = _released_receiver_return(PS_IPERF_LINE, IPERF_LOG)
    pid_text = PS_IPERF_LINE.split()[1]
    record = IperfProcess(pid=int(pid_text), log_file=IPERF_LOG)
    assert (record.pid, record.log_file) == released


def test_sender_session_signature() -> None:
    params = inspect.signature(IperfClient.start_sender_session).parameters
    assert params["window_bytes"].annotation == "int | None"
    assert params["window_bytes"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["ip_version"].annotation == "IpFamily | None"
    assert "window" not in params
    released = inspect.signature(IperfClient.start_traffic_sender).parameters  # type: ignore[deprecated]
    assert released["window"].annotation == "str | None"  # the released member is unchanged
    assert "window_bytes" not in released
    assert set(released) - {"window"} == set(params) - {"window_bytes"}


def test_receiver_session_signature() -> None:
    params = inspect.signature(IperfServer.start_receiver_session).parameters
    released = inspect.signature(IperfServer.start_traffic_receiver).parameters  # type: ignore[deprecated]
    assert set(params) == set(released)
    assert params["ip_version"].annotation == "IpFamily | None"


# --------------------------------------------------------------------------------------
# PingResult
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


def test_ping_result_accepts_the_tools_rounded_loss() -> None:
    assert PingResult("192.0.2.1", 3, 1, 66.6667).received == 1  # iputils prints 66.6667%
    assert PingResult("192.0.2.1", 0, 0, 0.0).transmitted == 0


def test_ping_json_output_is_documented_deprecated() -> None:
    doc = inspect.getdoc(IpRouting.ping) or ""
    assert "json_output" in doc and "ping_stats" in doc and "eprecated" in doc


# --------------------------------------------------------------------------------------
# NmapResult
# --------------------------------------------------------------------------------------


def test_nmap_result_from_a_scan_report() -> None:
    # what ``nmap -oX`` reports for a host with one open and one closed TCP port, as a
    # released implementer's normalised result lists it
    reported: list[tuple[int, str, str, str | None]] = [
        (22, "tcp", "open", "ssh"),
        (80, "tcp", "closed", None),
    ]
    result = NmapResult(
        up=True,
        addresses=("192.0.2.9",),
        ports=(
            NmapPort(22, TransportProtocol.TCP, NmapPortState.OPEN, "ssh"),
            NmapPort(80, TransportProtocol.TCP, NmapPortState.CLOSED, None),
        ),
    )
    assert [(p.port, str(p.protocol), str(p.state), p.service) for p in result.ports] == reported


def test_nmap_port_states_are_nmaps_six() -> None:
    assert [s.value for s in NmapPortState] == [
        "open",
        "closed",
        "filtered",
        "unfiltered",
        "open|filtered",
        "closed|filtered",
    ]


def test_scan_ports_signature() -> None:
    params = inspect.signature(NmapScanner.scan_ports).parameters
    assert params["ip_version"].annotation == "IpFamily"
    assert params["ports"].annotation == "Sequence[PortRange]"
    assert params["protocol"].annotation == "TransportProtocol | None"


# --------------------------------------------------------------------------------------
# ArpEntry
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


# --------------------------------------------------------------------------------------
# TransientEvent
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("event", "name", "kwargs"),
    [
        (Blackout(), "blackout", {}),
        (Brownout(loss_percent=50.0), "brownout", {"loss_percent": 50.0}),
        (
            Brownout(latency_ms=200, jitter_ms=10, loss_percent=5.0),
            "brownout",
            {"latency_ms": 200, "jitter_ms": 10, "loss_percent": 5.0},
        ),
        (LatencySpike(latency_ms=500), "latency_spike", {"spike_latency_ms": 500}),
        (
            LatencySpike(latency_ms=300, jitter_ms=100),
            "latency_spike",
            {"spike_latency_ms": 300, "jitter_ms": 100},
        ),
        (PacketStorm(loss_percent=10.0), "packet_storm", {"loss_percent": 10.0}),
        (PacketStorm(), "packet_storm", {}),
    ],
)
def test_transient_event_name_is_the_released_word(
    event: TransientEvent, name: str, kwargs: dict[str, float | int]
) -> None:
    assert event.event_name == name


def test_inject_event_signature() -> None:
    params = inspect.signature(NetemController.inject_event).parameters
    assert params["event"].annotation == "TransientEvent"
    assert params["duration_ms"].annotation == "int"


# --------------------------------------------------------------------------------------
# impairment profile parameter
# --------------------------------------------------------------------------------------


def test_netem_profile_parameter_has_no_any() -> None:
    for member in (NetemController.set_impairment_profile, NetemController.set_interface_profile):
        ann = inspect.signature(member).parameters["profile"].annotation
        assert ann == "ImpairmentProfile | dict[str, object]"


# --------------------------------------------------------------------------------------
# GroupRecord
# --------------------------------------------------------------------------------------


def _released_mld_args(
    records: Iterable[tuple[list[str], str, MulticastGroupRecordType]],
) -> str:
    """The released implementers' rendering (``_send_multicast_report``, as boardfarm has it)."""
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


# --------------------------------------------------------------------------------------
# The remaining Any
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
