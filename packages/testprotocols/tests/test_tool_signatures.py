"""Tool command-line strings become typed parameters: the declared signatures."""

from __future__ import annotations

import inspect
import shlex
import warnings
from datetime import datetime

import pytest
from testprotocols.device_management import DeviceManagement
from testprotocols.dns_client import DnsClient
from testprotocols.http_client import HttpClient
from testprotocols.ip_routing import IpRouting
from testprotocols.models import SnmpValueType
from testprotocols.nmap_scanner import NmapScanner
from testprotocols.ntp_client import NtpClient
from testprotocols.snmp_client import SnmpClient


def _sig(cls: type, name: str) -> inspect.Signature:
    return inspect.signature(getattr(cls, name))


def _kwonly(cls: type, name: str) -> dict[str, object]:
    return {
        p.name: p.default
        for p in _sig(cls, name).parameters.values()
        if p.kind is inspect.Parameter.KEYWORD_ONLY
    }


def test_declared_typed_parameters() -> None:
    assert _kwonly(IpRouting, "ping") == {}
    assert _kwonly(IpRouting, "traceroute") == {}
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


_NET_SNMP_TYPE_LETTERS = {
    SnmpValueType.INTEGER: "i",
    SnmpValueType.UNSIGNED: "u",
    SnmpValueType.OCTET_STRING: "s",
    SnmpValueType.OBJECT_IDENTIFIER: "o",
    SnmpValueType.IP_ADDRESS: "a",
    SnmpValueType.TIMETICKS: "t",
    SnmpValueType.BITS: "b",
}


class FakeSnmp:
    def __init__(self) -> None:
        self.commands: list[str] = []

    def execute_snmp_command(self, snmp_command: str, timeout: int = 30) -> str:
        warnings.warn(
            "execute_snmp_command is deprecated; use the typed snmp_* members",
            DeprecationWarning,
            stacklevel=2,
        )
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

    def snmp_set(
        self,
        host: str,
        oid: str,
        community: str,
        value: str,
        value_type: SnmpValueType,
        *,
        timeout_s: int = 10,
        retries: int = 3,
        command_timeout: int = 30,
    ) -> str:
        self.commands.append(
            f"snmpset -v 2c -On -c {community} -t {timeout_s} -r {retries} {host} {oid}"
            f" {_NET_SNMP_TYPE_LETTERS[value_type]} '{value}'"
        )
        return "out"

    def snmp_bulk_get(
        self,
        host: str,
        oid: str,
        community: str,
        *,
        non_repeaters: int = 0,
        max_repetitions: int = 10,
        timeout_s: int = 100,
        retries: int = 3,
        command_timeout: int = 30,
    ) -> str:
        self.commands.append(
            f"snmpbulkget -v2c -Cn{non_repeaters} -Cr{max_repetitions} -c {community}"
            f" -t {timeout_s} -r {retries} {host} {oid}"
        )
        return "out"


def test_snmp_members_are_declared_and_the_fake_conforms() -> None:
    assert {"snmp_get", "snmp_walk", "snmp_set", "snmp_bulk_get", "execute_snmp_command"} <= set(
        dir(SnmpClient)
    )
    client: SnmpClient = FakeSnmp()
    assert client.snmp_get("192.0.2.1", ".1.3.6.1.2.1.1.1.0", "private") == "out"
    with pytest.warns(DeprecationWarning, match="execute_snmp_command"):
        client.execute_snmp_command("snmpget -v 2c -c private 192.0.2.1 .1.3")  # type: ignore[deprecated]  # the released member under test
    sig = _sig(SnmpClient, "snmp_get")
    assert [p.name for p in sig.parameters.values()][:4] == ["self", "host", "oid", "community"]
    assert _kwonly(SnmpClient, "snmp_get") == {"timeout_s": 10, "retries": 3, "command_timeout": 30}
    assert _kwonly(SnmpClient, "snmp_set") == {"timeout_s": 10, "retries": 3, "command_timeout": 30}
    assert _kwonly(SnmpClient, "snmp_bulk_get") == {
        "non_repeaters": 0,
        "max_repetitions": 10,
        "timeout_s": 100,
        "retries": 3,
        "command_timeout": 30,
    }
    assert [p for p in _sig(SnmpClient, "snmp_set").parameters][:6] == [
        "self", "host", "oid", "community", "value", "value_type",
    ]  # fmt: skip
    assert client.snmp_set("192.0.2.1", ".1.3", "private", "5", SnmpValueType.INTEGER) == "out"
    assert client.snmp_bulk_get("192.0.2.1", "", "private") == "out"
    assert client.snmp_walk("192.0.2.1", "", "private") == "out"
    assert _kwonly(SnmpClient, "snmp_walk") == {
        "timeout_s": 100,
        "retries": 3,
        "command_timeout": 30,
    }


def test_every_snmp_value_type_has_a_net_snmp_letter() -> None:
    assert set(_NET_SNMP_TYPE_LETTERS) == set(SnmpValueType)


def test_snmp_set_takes_an_snmp_value_type() -> None:
    assert _sig(SnmpClient, "snmp_set").parameters["value_type"].annotation == "SnmpValueType"
    client = FakeSnmp()
    client.snmp_set("192.0.2.1", ".1.3", "private", "5", SnmpValueType.TIMETICKS)
    assert client.commands[-1].endswith(" t '5'")


def test_set_date_time_is_declared_and_set_date_is_deprecated() -> None:
    assert "set_date_time" in dir(NtpClient)
    assert [p for p in _sig(NtpClient, "set_date_time").parameters] == ["self", "value"]
    assert _sig(NtpClient, "set_date_time").parameters["value"].annotation == "datetime"
    assert [p for p in _sig(NtpClient, "set_date").parameters] == ["self", "opt", "date_string"]
    assert "Deprecated" in (NtpClient.set_date.__doc__ or "")  # type: ignore[deprecated]  # the released member under test


class _NtpWithoutSetDateTime:
    """Every NtpClient member but ``set_date_time``: the released setter only."""

    def get_date(self) -> str | None:
        return None

    def read_date(self) -> datetime | None:
        return None

    def set_date(self, opt: str, date_string: str) -> bool:
        return True

    def execute_time_sync(self, time_server: str) -> str:
        return ""


class _NtpWithSetDateTime(_NtpWithoutSetDateTime):
    def set_date_time(self, value: datetime) -> bool:
        return True


def test_a_driver_with_only_set_date_is_not_an_ntp_client() -> None:
    assert not isinstance(_NtpWithoutSetDateTime(), NtpClient)
    assert isinstance(_NtpWithSetDateTime(), NtpClient)


class ReleasedHost:
    """A driver with the released signatures only: no keyword-only parameters."""

    def __init__(self) -> None:
        self.argv: list[str] = []

    def http_get(self, url: str, timeout: int = 20, options: str = "") -> None:
        self.argv = ["curl", "-v", *shlex.split(options), "--connect-timeout", str(timeout), url]

    def curl(self, url: str, protocol: str, port: int | None = None, options: str = "") -> bool:
        self.argv = ["curl", "-v", *shlex.split(options), f"{protocol}://{url}"]
        return True

    def ping(
        self,
        ping_ip: str,
        ping_count: int = 4,
        ping_interface: str | None = None,
        options: str = "",
        timeout: int = 50,
        json_output: bool = False,
    ) -> bool:
        self.argv = ["ping", "-c", str(ping_count), ping_ip, *shlex.split(options)]
        return True


def test_a_released_signature_driver_behaves_as_before_for_released_calls() -> None:
    host = ReleasedHost()
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # a driver that predates the change never warns
        host.http_get("http://h/", 20, "--noproxy '*' -k -L")
        assert host.argv == [
            "curl", "-v", "--noproxy", "*", "-k", "-L", "--connect-timeout", "20", "http://h/",
        ]  # fmt: skip
        assert host.curl("h", "http", 80, "-k") is True
        assert host.argv == ["curl", "-v", "-k", "http://h"]
        host.ping("10.0.0.1", 2, None, "-W 2")
    assert host.argv == ["ping", "-c", "2", "10.0.0.1", "-W", "2"]
    # the typed keywords are the new part: a driver without them refuses a caller that passes one,
    # which is how a future caller detects a driver that predates them (inspect.signature or
    # catching this TypeError) and falls back to the option string.
    with pytest.raises(TypeError, match="no_proxy"):
        host.http_get("http://h/", no_proxy=True)  # type: ignore[call-arg]  # the unknown keyword is the check
    assert "no_proxy" not in inspect.signature(host.http_get).parameters
