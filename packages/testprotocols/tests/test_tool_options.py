"""Tool command-line strings become typed parameters (Phase 5b Task 9, O26 and O10)."""

from __future__ import annotations

import inspect
import shlex
import warnings
from datetime import datetime

import pytest
from testprotocols.deprecation import warn_renamed
from testprotocols.device_management import DeviceManagement
from testprotocols.dns_client import DnsClient
from testprotocols.http_client import HttpClient
from testprotocols.ip_routing import IpRouting
from testprotocols.nmap_scanner import NmapScanner
from testprotocols.ntp_client import NtpClient
from testprotocols.snmp_client import SnmpClient
from testprotocols.tool_options import (
    http_get_options,
    nmap_options,
    option_text,
    ping_options,
    settle_option_string,
    traceroute_options,
)


class FakeHost:
    """A minimal conforming driver for the tool members; records the argv it would run."""

    def __init__(self) -> None:
        self.argv: list[str] = []
        self.date: str | None = None

    def ping(
        self,
        ping_ip: str,
        ping_count: int = 4,
        ping_interface: str | None = None,
        options: str = "",
        timeout: int = 50,
        json_output: bool = False,
        *,
        reply_timeout_s: float | None = None,
        interval_s: float | None = None,
    ) -> bool:
        legacy = settle_option_string(
            options,
            what="ping(options)",
            typed={"reply_timeout_s": reply_timeout_s, "interval_s": interval_s},
        )
        extra = (
            shlex.split(options)
            if legacy
            else ping_options(reply_timeout_s=reply_timeout_s, interval_s=interval_s)
        )
        self.argv = ["ping", "-c", str(ping_count), ping_ip, *extra]
        return True

    def traceroute(
        self,
        host_ip: str,
        version: str = "",
        options: str = "",
        timeout: int = 60,
        *,
        numeric: bool = False,
    ) -> str:
        legacy = settle_option_string(
            options, what="traceroute(options)", typed={"numeric": numeric}
        )
        extra = shlex.split(options) if legacy else traceroute_options(numeric=numeric)
        self.argv = [f"traceroute{version}", *extra, host_ip]
        return ""

    def http_get(
        self,
        url: str,
        timeout: int = 20,
        options: str = "",
        *,
        no_proxy: bool = False,
        insecure: bool = False,
        follow_redirects: bool = False,
    ) -> None:
        typed = {"no_proxy": no_proxy, "insecure": insecure, "follow_redirects": follow_redirects}
        legacy = settle_option_string(options, what="http_get(options)", typed=typed)
        extra = shlex.split(options) if legacy else http_get_options(**typed)
        self.argv = ["curl", "-v", *extra, "--connect-timeout", str(timeout), url]

    def nmap(
        self,
        ipaddr: str,
        opts: str | None = None,
        *,
        fast: bool = False,
    ) -> None:
        legacy = settle_option_string(opts, what="nmap(opts)", typed={"fast": fast})
        extra = shlex.split(opts or "") if legacy else nmap_options(fast=fast)
        self.argv = ["nmap", "-Pn", "-r", *extra, ipaddr]

    def get_running_processes(self, ps_options: str = "-A") -> list[str]:
        settle_option_string(
            ps_options, what="get_running_processes(ps_options)", typed={}, default="-A"
        )
        self.argv = ["ps", *shlex.split(ps_options)]
        return []

    def dns_lookup(self, domain_name: str, record_type: str, opts: str = "") -> list[str]:
        settle_option_string(opts, what="dns_lookup(opts)", typed={})
        self.argv = ["dig", *shlex.split(opts), record_type, domain_name]
        return []


# --- test_old_option_string_still_works_and_warns ---------------------------------


def test_old_option_string_still_works_and_warns() -> None:
    host = FakeHost()
    with pytest.warns(DeprecationWarning, match=r"ping\(options\)"):
        host.ping("10.0.0.1", 4, None, "-W 2")
    assert host.argv == ["ping", "-c", "4", "10.0.0.1", "-W", "2"]
    with pytest.warns(DeprecationWarning, match="traceroute"):
        host.traceroute("10.0.0.1", "", "-n")
    assert host.argv == ["traceroute", "-n", "10.0.0.1"]
    with pytest.warns(DeprecationWarning, match="http_get"):
        host.http_get("http://h/", 20, "--noproxy '*' -k")
    assert host.argv == [
        "curl",
        "-v",
        "--noproxy",
        "*",
        "-k",
        "--connect-timeout",
        "20",
        "http://h/",
    ]
    with pytest.warns(DeprecationWarning, match="nmap"):
        host.nmap("10.0.0.1", "-F")
    assert host.argv == ["nmap", "-Pn", "-r", "-F", "10.0.0.1"]


def test_option_string_with_no_typed_replacement_still_warns() -> None:
    host = FakeHost()
    with pytest.warns(DeprecationWarning, match="no typed replacement"):
        host.dns_lookup("example.org", "A", "+short")
    assert host.argv == ["dig", "+short", "A", "example.org"]
    with pytest.warns(DeprecationWarning, match="no typed replacement"):
        host.get_running_processes("-ef")
    assert host.argv == ["ps", "-ef"]


def test_default_and_empty_options_do_not_warn() -> None:
    host = FakeHost()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        host.ping("10.0.0.1")
        host.traceroute("10.0.0.1", "6")
        host.http_get("http://h/")
        host.nmap("10.0.0.1", None)
        host.get_running_processes()
        host.get_running_processes("-A")  # the released default is not a deprecated spelling
        host.dns_lookup("example.org", "A")
    assert host.argv == ["dig", "A", "example.org"]


def test_warning_points_at_the_callers_line() -> None:
    host = FakeHost()
    with pytest.warns(DeprecationWarning) as record:
        host.ping("10.0.0.1", 4, None, "-W 2")
    assert record[0].filename == __file__


# --- test_typed_params_give_the_same_effect ---------------------------------------


def test_typed_params_give_the_same_effect() -> None:
    typed, legacy = FakeHost(), FakeHost()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        typed.ping("10.0.0.1", reply_timeout_s=2, interval_s=0.2)
    with pytest.warns(DeprecationWarning):
        legacy.ping("10.0.0.1", 4, None, "-W 2 -i 0.2")
    assert typed.argv == legacy.argv

    typed, legacy = FakeHost(), FakeHost()
    typed.traceroute("10.0.0.1", numeric=True)
    with pytest.warns(DeprecationWarning):
        legacy.traceroute("10.0.0.1", "", "-n")
    assert typed.argv == legacy.argv

    typed, legacy = FakeHost(), FakeHost()
    typed.http_get("http://h/", no_proxy=True, insecure=True, follow_redirects=True)
    with pytest.warns(DeprecationWarning):
        legacy.http_get("http://h/", 20, "--noproxy '*' -k -L")
    assert typed.argv == legacy.argv

    typed, legacy = FakeHost(), FakeHost()
    typed.nmap("10.0.0.1", fast=True)
    with pytest.warns(DeprecationWarning):
        legacy.nmap("10.0.0.1", "-F")
    assert typed.argv == legacy.argv


def test_renderers_give_the_option_string_a_pre_typed_driver_receives() -> None:
    assert option_text(http_get_options(no_proxy=True, insecure=True, follow_redirects=True)) == (
        "--noproxy '*' -k -L"  # what the released use case built, modulo the trailing blank
    )
    assert option_text(ping_options(reply_timeout_s=2.0, interval_s=0.25)) == "-W 2 -i 0.25"
    assert ping_options() == traceroute_options() == http_get_options() == nmap_options() == []


@pytest.mark.parametrize("bad", [0, -1, 0.0])
def test_non_positive_seconds_raise_value_error(bad: float) -> None:
    with pytest.raises(ValueError, match="reply_timeout_s"):
        ping_options(reply_timeout_s=bad)


def test_non_number_seconds_raise_type_error() -> None:
    with pytest.raises(TypeError, match="interval_s"):
        ping_options(interval_s=True)
    with pytest.raises(TypeError, match="reply_timeout_s"):
        ping_options(reply_timeout_s="2")  # type: ignore[arg-type]


# --- test_both_forms_raise --------------------------------------------------------


def test_both_forms_raise() -> None:
    host = FakeHost()
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # raises ValueError before any warning
        with pytest.raises(ValueError, match="reply_timeout_s"):
            host.ping("10.0.0.1", 4, None, "-W 2", reply_timeout_s=2)
        with pytest.raises(ValueError, match="numeric"):
            host.traceroute("10.0.0.1", "", "-n", numeric=True)
        with pytest.raises(ValueError, match="no_proxy"):
            host.http_get("http://h/", 20, "-k", no_proxy=True)
        with pytest.raises(ValueError, match="fast"):
            host.nmap("10.0.0.1", "-F", fast=True)
    assert host.argv == []


def test_a_false_flag_is_not_given() -> None:
    with pytest.warns(DeprecationWarning):
        assert settle_option_string("-k", what="x", typed={"insecure": False}) is True
    assert settle_option_string("", what="x", typed={"insecure": True}) is False
    assert settle_option_string(None, what="x", typed={"fast": True}) is False


def test_option_string_must_be_a_str() -> None:
    with pytest.raises(TypeError, match="takes a str"):
        settle_option_string(["-k"], what="x", typed={})  # type: ignore[arg-type]


# --- the contracts ----------------------------------------------------------------


def _sig(cls: type, name: str) -> inspect.Signature:
    return inspect.signature(getattr(cls, name))


def _kwonly(cls: type, name: str) -> dict[str, object]:
    return {
        p.name: p.default
        for p in _sig(cls, name).parameters.values()
        if p.kind is inspect.Parameter.KEYWORD_ONLY
    }


def test_declared_typed_parameters() -> None:
    assert _kwonly(IpRouting, "ping") == {"reply_timeout_s": None, "interval_s": None}
    assert _kwonly(IpRouting, "traceroute") == {"numeric": False}
    assert _kwonly(HttpClient, "http_get") == {
        "no_proxy": False,
        "insecure": False,
        "follow_redirects": False,
    }
    assert _kwonly(HttpClient, "curl") == {
        "no_proxy": False,
        "insecure": False,
        "follow_redirects": False,
    }
    assert _kwonly(NmapScanner, "nmap") == {"fast": False}
    assert _kwonly(NmapScanner, "scan_ports")["fast"] is False
    assert _kwonly(DnsClient, "dns_lookup") == {}
    assert _kwonly(DeviceManagement, "get_running_processes") == {}


def test_released_positions_and_types_are_unchanged() -> None:
    def positional(cls: type, name: str) -> list[tuple[str, object]]:
        return [
            (p.name, p.default)
            for p in _sig(cls, name).parameters.values()
            if p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD and p.name != "self"
        ]

    assert positional(IpRouting, "ping") == [
        ("ping_ip", inspect.Parameter.empty),
        ("ping_count", 4),
        ("ping_interface", None),
        ("options", ""),
        ("timeout", 50),
        ("json_output", False),
    ]
    assert positional(IpRouting, "traceroute")[-2:] == [("options", ""), ("timeout", 60)]
    assert positional(HttpClient, "curl")[-1] == ("options", "")
    assert positional(HttpClient, "http_get")[-2:] == [("timeout", 20), ("options", "")]
    assert positional(NmapScanner, "nmap")[-2:] == [("opts", None), ("timeout", 30)]
    assert positional(DeviceManagement, "get_running_processes") == [("ps_options", "-A")]
    for cls, name, param in [
        (IpRouting, "ping", "options"),
        (IpRouting, "traceroute", "options"),
        (HttpClient, "curl", "options"),
        (HttpClient, "http_get", "options"),
        (DnsClient, "dns_lookup", "opts"),
        (DeviceManagement, "get_running_processes", "ps_options"),
    ]:
        assert _sig(cls, name).parameters[param].annotation == "str"


# --- new members: SNMP and date ---------------------------------------------------


class FakeSnmp:
    def __init__(self) -> None:
        self.commands: list[str] = []

    def execute_snmp_command(self, snmp_command: str, timeout: int = 30) -> str:
        warn_renamed("execute_snmp_command", "snmp_get or snmp_walk")
        self.commands.append(snmp_command)
        return "out"

    def snmp_get(
        self,
        host: str,
        oid: str,
        community: str,
        *,
        timeout_s: int = 10,
        retries: int = 3,
        command_timeout: int = 30,
    ) -> str:
        self.commands.append(
            f"snmpget -v 2c -On -c {community} -t {timeout_s} -r {retries} {host} {oid}"
        )
        return "out"

    def snmp_walk(
        self,
        host: str,
        oid: str,
        community: str,
        *,
        timeout_s: int = 100,
        retries: int = 3,
        command_timeout: int = 30,
    ) -> str:
        self.commands.append(
            f"snmpwalk -v 2c -On -c {community} -t {timeout_s} -r {retries} {host} {oid}"
        )
        return "out"


def test_snmp_members_are_declared_and_the_fake_conforms() -> None:
    assert {"snmp_get", "snmp_walk", "execute_snmp_command"} <= set(dir(SnmpClient))
    client: SnmpClient = FakeSnmp()
    assert client.snmp_get("192.0.2.1", ".1.3.6.1.2.1.1.1.0", "private") == "out"
    with pytest.warns(DeprecationWarning, match="execute_snmp_command"):
        client.execute_snmp_command("snmpget -v 2c -c private 192.0.2.1 .1.3")
    sig = _sig(SnmpClient, "snmp_get")
    assert [p.name for p in sig.parameters.values()][:4] == ["self", "host", "oid", "community"]
    assert _kwonly(SnmpClient, "snmp_get") == {"timeout_s": 10, "retries": 3, "command_timeout": 30}
    assert _kwonly(SnmpClient, "snmp_walk") == {
        "timeout_s": 100,
        "retries": 3,
        "command_timeout": 30,
    }


def test_set_date_time_is_declared_and_set_date_is_deprecated() -> None:
    assert "set_date_time" in dir(NtpClient)
    assert [p for p in _sig(NtpClient, "set_date_time").parameters] == ["self", "value"]
    assert _sig(NtpClient, "set_date_time").parameters["value"].annotation == "datetime"
    assert [p for p in _sig(NtpClient, "set_date").parameters] == ["self", "opt", "date_string"]
    assert "Deprecated" in (NtpClient.set_date.__doc__ or "")
    assert isinstance(datetime.now(), datetime)
