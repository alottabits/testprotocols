"""Host-tool and service vocabularies."""

from __future__ import annotations

import dataclasses
import inspect
import typing
import warnings

import pytest
from testprotocols.dns_client import DnsClient
from testprotocols.http_client import HttpClient
from testprotocols.http_server import HttpServer
from testprotocols.ip_interface import IpInterface
from testprotocols.ip_routing import IpRouting
from testprotocols.iperf_client import IperfClient
from testprotocols.iperf_server import IperfServer
from testprotocols.models import (
    DnsRecordType,
    HTTPResult,
    HttpScheme,
    IpFamily,
    IpVersion,
    LinkAdminState,
    MeasurementSpec,
    PageCompletion,
    PortMappingProtocol,
    QoeCompletion,
    QoEResult,
    QoeScenario,
    QoeTool,
    ServiceStatus,
    StormControlConfig,
    StormControlType,
    StormControlUnit,
    TrafficSpec,
    TransportProtocol,
)
from testprotocols.nmap_scanner import NmapScanner
from testprotocols.qoe_browser import QoeBrowser
from testprotocols.radius_server import RadiusServer
from testprotocols.upnp_client import UpnpClient
from testprotocols.vlan_client import VlanClient


def _values(enum_type: type[object]) -> list[object]:
    return [m.value for m in enum_type]  # type: ignore[attr-defined]  # `enum_type` is typed `type[object]`


def _equal(left: object, right: object) -> bool:
    """``left == right`` without the type checker's strict-equality narrowing."""
    return left == right


def _stub(self: object, *args: object, **kwargs: object) -> None:
    return None


def _ann(fn: object, name: str) -> object:
    return inspect.signature(fn).parameters[name].annotation  # type: ignore[arg-type]  # `fn` is any member, typed `object`


# --- members equal their released strings -----------------------------------------


def test_enum_members() -> None:
    assert _values(IpVersion) == ["ipv4", "ipv6"]
    assert _values(DnsRecordType) == [
        "A", "AAAA", "CNAME", "MX", "NS", "PTR", "SOA", "SRV", "TXT",
    ]  # fmt: skip
    assert _values(HttpScheme) == ["http", "https"]
    assert _values(LinkAdminState) == ["up", "down"]
    assert _values(QoeTool) == ["browser", "http_client", "webrtc", "tcp_probe"]
    assert _values(PageCompletion) == ["load", "domcontentloaded", "networkidle", "commit"]
    assert _values(QoeCompletion) == [*_values(PageCompletion), "duration", "response", "connect"]
    assert _values(QoeScenario) == ["page_load"]
    assert _values(TransportProtocol) == ["tcp", "udp"]
    assert _values(ServiceStatus) == ["running", "stopped", "error"]
    assert _values(StormControlUnit) == ["percent", "pps"]


def test_ip_family_is_an_int_enum_for_the_iperf_options() -> None:
    assert [m.value for m in IpFamily] == [4, 6]
    assert f"-{IpFamily.V4}" == "-4" and f"-{IpFamily.V6}" == "-6"  # how a driver formats it
    assert _equal(IpFamily.V6, 6)
    assert IpFamily(4) is IpFamily.V4  # an int naming a member is its value


def test_qoe_defaults_repr_as_their_quoted_text() -> None:
    spec = MeasurementSpec()
    # the example implementer builds its script with repr(spec.completion)
    script = "wait_until={wait_until_repr}".replace("{wait_until_repr}", repr(spec.completion))
    assert script == "wait_until='networkidle'"
    assert repr(spec.tool) == "'browser'"
    assert str(QoeCompletion.LOAD) == "load"


# --- protocol signatures ------------------------------------------------------------


@pytest.mark.parametrize(
    ("fn", "param", "ann"),
    [
        (DnsClient.dns_lookup, "record_type", "DnsRecordType | str"),  # type: ignore[deprecated]  # the released member under test
        (DnsClient.resolve, "record_type", "DnsRecordType | str"),
        (HttpClient.curl, "protocol", "HttpScheme | str"),
        (HttpServer.start_http_service, "port", "str"),
        (HttpServer.start_http_service, "ip_version", "str"),
        (HttpServer.stop_http_service, "port", "str"),
        (IperfClient.start_traffic_sender, "ip_version", "IpFamily | int | None"),  # type: ignore[deprecated]  # the released member under test
        (IperfServer.start_traffic_receiver, "ip_version", "IpFamily | int | None"),  # type: ignore[deprecated]  # the released member under test
        (IpInterface.set_link_state, "state", "LinkAdminState | str"),
        (IpRouting.traceroute, "version", "str"),
        (NmapScanner.nmap, "ip_type", "IpVersion | str"),  # type: ignore[deprecated]  # the released member under test
        (UpnpClient.create_upnp_rule, "int_port", "str"),
        (UpnpClient.create_upnp_rule, "ext_port", "str"),
        (UpnpClient.create_upnp_rule, "protocol", "PortMappingProtocol | str"),
        (UpnpClient.delete_upnp_rule, "ext_port", "str"),
        (UpnpClient.delete_upnp_rule, "protocol", "PortMappingProtocol | str"),
        (VlanClient.add_vlan_interface, "vlan_id", "str"),
        (VlanClient.delete_vlan_interface, "vlan_id", "str"),
        (QoeBrowser.measure_productivity, "scenario", "QoeScenario | str"),
        (QoeBrowser.measure_productivity, "wait_until", "PageCompletion | str"),
    ],
)
def test_parameter_annotations(fn: object, param: str, ann: str) -> None:
    assert _ann(fn, param) == ann


def test_defaults_are_unchanged_text() -> None:
    assert inspect.signature(IpRouting.traceroute).parameters["version"].default == ""
    assert inspect.signature(QoeBrowser.measure_productivity).parameters["scenario"].default == (
        "page_load"
    )
    wait_until = inspect.signature(QoeBrowser.measure_productivity).parameters["wait_until"]
    assert wait_until.default == "networkidle"


def test_nmap_protocol_and_port_stay_as_released() -> None:
    assert _ann(NmapScanner.nmap, "protocol") == "str | None"  # type: ignore[deprecated]  # the released member under test
    assert _ann(NmapScanner.nmap, "port") == "str | int | None"  # type: ignore[deprecated]  # the released member under test


def test_upnp_protocol_is_the_firewall_port_mapping_protocol() -> None:
    assert _ann(UpnpClient.create_upnp_rule, "protocol") == "PortMappingProtocol | str"
    assert [m.value for m in PortMappingProtocol][:2] == ["tcp", "udp"]
    assert "TCP_UDP" in (UpnpClient.create_upnp_rule.__doc__ or "")


def test_ip_interface_stub_with_every_released_member_does_not_have_the_new_one() -> None:
    released = [
        name for name in dir(IpInterface) if not name.startswith("_") and name != "is_link_admin_up"
    ]

    class Released:  # a released implementer: every member but the new one
        pass

    for name in released:
        setattr(Released, name, _stub)

    assert callable(IpInterface.is_link_admin_up)
    assert list(inspect.signature(IpInterface.is_link_admin_up).parameters) == ["self", "interface"]
    assert inspect.signature(IpInterface.is_link_up).parameters["pattern"].default == (
        "BROADCAST,MULTICAST,UP"
    )
    assert "set_link_state" in released and "is_link_up" in released
    assert not isinstance(Released(), IpInterface)
    Released.is_link_admin_up = _stub  # type: ignore[attr-defined]  # adding the member at run time is the check
    assert isinstance(Released(), IpInterface)


def test_radius_get_status_stays_str_and_is_announced() -> None:
    assert inspect.signature(RadiusServer.get_status).return_annotation == "str"
    assert "ServiceStatus" in (RadiusServer.get_status.__doc__ or "")


# --- HTTPResult --------------------------------------------------------------------

_RESPONSE = "HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello"


def test_http_result_is_the_released_class() -> None:
    """Not a dataclass; the released attributes are plain and assignable; identity equality."""
    result = HTTPResult(_RESPONSE)
    assert not dataclasses.is_dataclass(result)
    assert (result.raw, result.code, result.beautified_text) == (_RESPONSE, "200", "hello")
    assert HTTPResult(response=_RESPONSE) is not result
    assert HTTPResult(_RESPONSE) != result
    result.code = "404"
    result.beautified_text = "gone"
    assert (result.code, result.beautified_text) == ("404", "gone")


def test_http_result_typed_reads() -> None:
    result = HTTPResult(_RESPONSE)
    assert (result.status, result.body) == (200, "hello")
    status = inspect.getattr_static(HTTPResult, "status")
    assert isinstance(status, property)
    assert typing.get_type_hints(status.fget)["return"] == int | None


def test_http_result_typed_reads_follow_the_released_attributes() -> None:
    result = HTTPResult(_RESPONSE)
    result.code = "503"
    result.beautified_text = "busy"
    assert (result.status, result.body) == (503, "busy")


def test_http_result_typed_reads_are_read_only() -> None:
    result = HTTPResult(_RESPONSE)
    with pytest.raises(AttributeError):
        result.status = 404  # type: ignore[misc]  # assigning a frozen field is the check
    with pytest.raises(AttributeError):
        result.body = "x"  # type: ignore[misc]  # assigning a frozen field is the check


def test_http_result_reads_do_not_warn() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = HTTPResult("HTTP/1.1 404 Not Found\n\nmissing")
        assert (result.status, result.body, result.code) == (404, "missing", "404")


@pytest.mark.parametrize("text", ["", "garbage", "HTTP/1.1", "HTTP/1.1 abc Weird\n\nx"])
def test_http_result_without_a_numeric_status(text: str) -> None:
    result = HTTPResult(text)  # the released parser never raised
    assert result.status is None
    assert result.raw == text


@pytest.mark.parametrize("code", ["99", "600", "0", "1000", "\uff12\uff10\uff10"])
def test_http_result_status_outside_100_to_599_is_none(code: str) -> None:
    result = HTTPResult(f"HTTP/1.1 {code} Odd\n\nx")
    assert result.status is None
    assert result.code == code  # the released text is unchanged


def test_http_result_non_numeric_code_text_is_kept_in_the_released_attribute() -> None:
    assert HTTPResult("HTTP/1.1 abc Weird\n\nx").code == "abc"


def test_http_result_subclass_assigning_attributes_still_works() -> None:
    class Patched(HTTPResult):
        def __init__(self, response: str) -> None:
            super().__init__(response)
            self.code = "200"

    assert Patched("garbage").status == 200


# --- QoEResult.protocol --------------------------------------------------------------


def test_qoe_result_protocol_is_the_device_word_stored_as_given() -> None:
    assert QoEResult().protocol is None
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        for word in ("h2", "h3", "http/1.1", "http/1.0"):
            assert QoEResult(protocol=word).protocol == word
    result = QoEResult(protocol="h2c")
    assert dataclasses.replace(result, success=False).protocol == "h2c"
    result.protocol = None
    assert result.protocol is None


# --- MeasurementSpec ---------------------------------------------------------------


def test_measurement_spec_defaults_equal_released_text() -> None:
    spec = MeasurementSpec()
    assert type(spec.tool) is str and _equal(spec.tool, QoeTool.BROWSER)  # the released default
    assert type(spec.completion) is str
    assert _equal(spec.completion, QoeCompletion.NETWORKIDLE)


def test_measurement_spec_plain_strings_are_stored_as_given() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        spec = MeasurementSpec(tool="http_client", completion="duration", duration_s=15)
        spec.tool = "webrtc"
        page = MeasurementSpec(completion=PageCompletion.LOAD)
    assert type(spec.tool) is str and spec.tool == QoeTool.WEBRTC
    assert spec.completion == QoeCompletion.DURATION
    assert page.completion is PageCompletion.LOAD and _equal(page.completion, QoeCompletion.LOAD)


# --- TrafficSpec -------------------------------------------------------------------


def test_traffic_spec_protocol() -> None:
    default = TrafficSpec("10.0.0.1", 1.0).protocol
    assert type(default) is str and _equal(default, TransportProtocol.UDP)  # the released default
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        spec = TrafficSpec("10.0.0.1", 1.0, protocol="tcp")
    assert type(spec.protocol) is str and _equal(spec.protocol, TransportProtocol.TCP)


# --- StormControlConfig ------------------------------------------------------------


def test_storm_control_unit_is_an_addition() -> None:
    config = StormControlConfig("1", {StormControlType.BROADCAST: 10.0})
    assert config.unit is None
    assert StormControlConfig("1", unit=StormControlUnit.PPS).unit is StormControlUnit.PPS
    assert [f.name for f in dataclasses.fields(StormControlConfig)] == [
        "port",
        "thresholds",
        "unit",
    ]
