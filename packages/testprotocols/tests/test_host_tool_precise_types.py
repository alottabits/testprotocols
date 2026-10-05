"""Host-tool and service vocabularies."""

from __future__ import annotations

import dataclasses
import inspect
import warnings

import pytest
from testprotocols.deprecation import coerce_enum
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
    parse_http_response,
)
from testprotocols.nmap_scanner import NmapScanner
from testprotocols.qoe_browser import QoeBrowser
from testprotocols.radius_server import RadiusServer
from testprotocols.upnp_client import UpnpClient
from testprotocols.vlan_client import VlanClient


def _values(enum_type: type[object]) -> list[object]:
    return [m.value for m in enum_type]  # type: ignore[attr-defined]


def _equal(left: object, right: object) -> bool:
    """``left == right`` without the type checker's strict-equality narrowing."""
    return left == right


def _stub(self: object, *args: object, **kwargs: object) -> None:
    return None


def _ann(fn: object, name: str) -> object:
    return inspect.signature(fn).parameters[name].annotation  # type: ignore[arg-type]


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
    with warnings.catch_warnings():
        warnings.simplefilter(
            "error"
        )  # an int naming a member is its value, not a deprecated spelling
        assert coerce_enum(IpFamily, 4, what="ip_version") is IpFamily.V4
        assert coerce_enum(IpFamily, IpFamily.V6, what="ip_version") is IpFamily.V6
    with pytest.raises(ValueError, match="ip_version"):
        coerce_enum(IpFamily, 5, what="ip_version")  # a number naming no member: a bad value
    for wrong in (True, 4.0):  # a bool or a float is a wrong type
        with pytest.raises(TypeError, match="ip_version"):
            coerce_enum(IpFamily, wrong, what="ip_version")  # type: ignore[arg-type]


def test_qoe_enums_used_in_generated_text_repr_as_their_quoted_text() -> None:
    spec = MeasurementSpec(tool=QoeTool.BROWSER, completion=QoeCompletion.LOAD)
    # the example implementer builds its script with repr(spec.completion)
    script = "wait_until={wait_until_repr}".replace("{wait_until_repr}", repr(spec.completion))
    assert script == "wait_until='load'"
    assert repr(spec.tool) == "'browser'"
    assert repr(QoeCompletion.RESPONSE) == "'response'"
    # the other enums keep the default repr
    assert repr(IpVersion.IPV4) == "<IpVersion.IPV4: 'ipv4'>"
    assert repr(PageCompletion.LOAD) == "<PageCompletion.LOAD: 'load'>"
    assert str(QoeCompletion.LOAD) == "load"


# --- protocol signatures ------------------------------------------------------------


@pytest.mark.parametrize(
    ("fn", "param", "ann"),
    [
        (DnsClient.dns_lookup, "record_type", "DnsRecordType | str"),
        (DnsClient.resolve, "record_type", "DnsRecordType | str"),
        (HttpClient.curl, "protocol", "HttpScheme | str"),
        (HttpServer.start_http_service, "port", "str"),
        (HttpServer.start_http_service, "ip_version", "str"),
        (HttpServer.stop_http_service, "port", "str"),
        (IperfClient.start_traffic_sender, "ip_version", "IpFamily | int | None"),
        (IperfServer.start_traffic_receiver, "ip_version", "IpFamily | int | None"),
        (IpInterface.set_link_state, "state", "LinkAdminState | str"),
        (IpRouting.traceroute, "version", "str"),
        (NmapScanner.nmap, "ip_type", "IpVersion | str"),
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
    assert _ann(NmapScanner.nmap, "protocol") == "str | None"
    assert _ann(NmapScanner.nmap, "port") == "str | int | None"


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
    Released.is_link_admin_up = _stub  # type: ignore[attr-defined]
    assert isinstance(Released(), IpInterface)


def test_radius_get_status_stays_str_and_is_announced() -> None:
    assert inspect.signature(RadiusServer.get_status).return_annotation == "str"
    assert "ServiceStatus" in (RadiusServer.get_status.__doc__ or "")


# --- HTTPResult --------------------------------------------------------------------

_RESPONSE = "HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello"


def test_http_result_released_constructor_and_typed_attributes() -> None:
    result = HTTPResult(_RESPONSE)
    assert (result.status, result.body, result.raw) == (200, "hello", _RESPONSE)
    assert HTTPResult(response=_RESPONSE) == result
    assert parse_http_response(_RESPONSE) == result
    assert dataclasses.is_dataclass(result)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.status = 404  # type: ignore[misc]


def test_http_result_released_attributes_warn_but_work() -> None:
    result = HTTPResult(_RESPONSE)
    with pytest.warns(DeprecationWarning, match="HTTPResult.code") as record:
        assert result.code == "200"
    assert record[0].filename == __file__
    with pytest.warns(DeprecationWarning, match="beautified_text"):
        assert result.beautified_text == "hello"
    assert result.raw == _RESPONSE  # released attribute, not deprecated


def test_http_result_typed_attributes_do_not_warn() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = HTTPResult("HTTP/1.1 404 Not Found\n\nmissing")
        assert (result.status, result.body) == (404, "missing")


@pytest.mark.parametrize("text", ["", "garbage", "HTTP/1.1", "HTTP/1.1 abc Weird\n\nx"])
def test_http_result_without_a_numeric_status(text: str) -> None:
    result = HTTPResult(text)  # the released parser never raised
    assert result.status == 0
    assert result.raw == text


@pytest.mark.parametrize("code", ["99", "600", "0", "1000"])
def test_http_result_status_outside_100_to_599_is_no_status(code: str) -> None:
    result = HTTPResult(f"HTTP/1.1 {code} Odd\n\nx")
    assert result.status == 0
    with pytest.warns(DeprecationWarning):
        assert result.code == code  # the released text is unchanged


def test_http_result_equality_is_by_value() -> None:
    assert HTTPResult(_RESPONSE) == HTTPResult(_RESPONSE)
    assert HTTPResult(_RESPONSE) != HTTPResult("HTTP/1.1 500 Err\n\nx")
    assert len({HTTPResult(_RESPONSE), HTTPResult(_RESPONSE)}) == 1


def test_http_result_non_numeric_code_text_is_kept_in_the_released_attribute() -> None:
    with pytest.warns(DeprecationWarning):
        assert HTTPResult("HTTP/1.1 abc Weird\n\nx").code == "abc"


def test_http_result_rejects_non_text() -> None:
    with pytest.raises(TypeError, match="response text"):
        HTTPResult(None)  # type: ignore[arg-type]


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
    assert spec.tool is QoeTool.BROWSER and _equal(spec.tool, "browser")
    assert spec.completion is QoeCompletion.NETWORKIDLE
    assert _equal(spec.completion, "networkidle")


def test_measurement_spec_plain_strings_warn_and_convert() -> None:
    with pytest.warns(DeprecationWarning) as record:
        spec = MeasurementSpec(tool="http_client", completion="duration", duration_s=15)
    assert [str(w.message).split(":")[0] for w in record] == [
        "MeasurementSpec.tool",
        "MeasurementSpec.completion",
    ]
    assert all(w.filename == __file__ for w in record)
    assert spec.tool is QoeTool.HTTP_CLIENT
    assert spec.completion is QoeCompletion.DURATION
    with pytest.warns(DeprecationWarning):
        spec.tool = "webrtc"
    assert spec.tool is QoeTool.WEBRTC


def test_measurement_spec_page_completion_converts_silently() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        spec = MeasurementSpec(completion=PageCompletion.LOAD)
    assert spec.completion is QoeCompletion.LOAD


def test_measurement_spec_unknown_word_is_refused() -> None:
    with pytest.raises(ValueError, match="bogus"):
        MeasurementSpec(tool="bogus")
    with pytest.raises(ValueError, match="idle"):
        MeasurementSpec(completion="idle")


# --- TrafficSpec -------------------------------------------------------------------


def test_traffic_spec_protocol() -> None:
    assert TrafficSpec("10.0.0.1", 1.0).protocol is TransportProtocol.UDP
    with pytest.warns(DeprecationWarning, match="TransportProtocol.TCP") as record:
        spec = TrafficSpec("10.0.0.1", 1.0, protocol="tcp")
    assert record[0].filename == __file__
    assert spec.protocol is TransportProtocol.TCP and _equal(spec.protocol, "tcp")
    spec.protocol = TransportProtocol.UDP
    with pytest.raises(ValueError, match="icmp"):
        spec.protocol = "icmp"
    assert spec.protocol is TransportProtocol.UDP


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
