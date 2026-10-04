"""Host-tool and service vocabularies (Phase 5b Task 7)."""

from __future__ import annotations

import dataclasses
import inspect
import warnings

import pytest
from testprotocols.deprecation import coerce_enum, coerce_open_enum
from testprotocols.dns_client import DnsClient
from testprotocols.http_client import HttpClient
from testprotocols.http_server import HttpServer
from testprotocols.ip_interface import IpInterface
from testprotocols.ip_routing import IpRouting
from testprotocols.iperf_client import IperfClient
from testprotocols.iperf_server import IperfServer
from testprotocols.models import (
    AcctStatusType,
    AcctTerminateCause,
    DnsRecordType,
    EapMethod,
    HTTPResult,
    HttpScheme,
    HttpVersion,
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
    RadiusAccountingRecord,
    RadiusUser,
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
        "A", "AAAA", "CNAME", "MX", "NS", "PTR", "SOA", "SRV", "TXT", "other",
    ]  # fmt: skip
    assert _values(HttpScheme) == ["http", "https"]
    assert _values(LinkAdminState) == ["up", "down"]
    assert _values(QoeTool) == ["browser", "http_client", "webrtc", "tcp_probe"]
    assert _values(PageCompletion) == ["load", "domcontentloaded", "networkidle", "commit"]
    assert _values(QoeCompletion) == [*_values(PageCompletion), "duration", "response", "connect"]
    assert _values(QoeScenario) == ["page_load"]
    assert _values(HttpVersion) == ["http/1.1", "h2", "h3", "other"]
    assert _values(TransportProtocol) == ["tcp", "udp"]
    assert {"Start", "Interim-Update", "Stop"} <= set(_values(AcctStatusType))
    assert _values(ServiceStatus) == ["running", "stopped", "error"]
    assert _values(StormControlUnit) == ["percent", "pps"]
    assert EapMethod("PEAP-MSCHAPv2") is EapMethod.PEAP_MSCHAPV2  # the released docstring words
    assert EapMethod("TTLS-PAP") is EapMethod.TTLS_PAP


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
    for bad in (5, True, 4.0):
        with pytest.raises(ValueError, match="ip_version"):
            coerce_enum(IpFamily, bad, what="ip_version")  # type: ignore[arg-type]


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


# --- HTTPResult (M20) ---------------------------------------------------------------

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


# --- QoEResult.protocol (M22, shape 3o with None) -----------------------------------


def test_qoe_result_defaults_and_member() -> None:
    assert QoEResult().protocol is None
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = QoEResult(protocol=HttpVersion.H2)
    assert result.protocol is HttpVersion.H2
    assert result.protocol_raw is None


def test_qoe_result_plain_string_naming_a_member_warns_and_converts() -> None:
    with pytest.warns(DeprecationWarning, match="HttpVersion.H3") as record:
        result = QoEResult(protocol="h3")
    assert record[0].filename == __file__
    assert result.protocol is HttpVersion.H3
    assert _equal(result.protocol, "h3")  # the released comparison still holds
    with pytest.warns(DeprecationWarning, match="HttpVersion.H1"):
        assert QoEResult(protocol="http/1.1").protocol is HttpVersion.H1


def test_qoe_result_browser_words_warn_and_a_driver_avoids_it_with_coerce_open_enum() -> None:
    for word in ("h2", "h3", "http/1.1"):  # the words a browser reports as the next hop
        with pytest.warns(DeprecationWarning, match="HttpVersion"):
            QoEResult(protocol=word)
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        member, raw = coerce_open_enum(
            HttpVersion, "http/1.0", what="protocol", other=HttpVersion.OTHER
        )
        result = QoEResult(protocol=member, protocol_raw=raw)
    assert (result.protocol, result.protocol_raw) == (HttpVersion.OTHER, "http/1.0")


def test_qoe_result_unknown_protocol_word_is_other_and_keeps_raw() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = QoEResult(protocol="http/1.0")
    assert result.protocol is HttpVersion.OTHER
    assert result.protocol_raw == "http/1.0"


def test_qoe_result_replace_and_assignment_agree() -> None:
    result = QoEResult(protocol="h2c")
    changed = dataclasses.replace(result, protocol=HttpVersion.H3)
    assert (changed.protocol, changed.protocol_raw) == (HttpVersion.H3, None)
    other = dataclasses.replace(result, protocol="quic")
    assert (other.protocol, other.protocol_raw) == (HttpVersion.OTHER, "quic")
    kept = dataclasses.replace(result, success=False)
    assert (kept.protocol, kept.protocol_raw) == (HttpVersion.OTHER, "h2c")
    result.protocol = None
    assert (result.protocol, result.protocol_raw) == (None, None)
    result.protocol = HttpVersion.H2
    assert result.protocol_raw is None


def test_qoe_result_inconsistent_raw_is_refused() -> None:
    with pytest.raises(ValueError, match="protocol_raw"):
        QoEResult(protocol=HttpVersion.H2, protocol_raw="h2c")
    with pytest.raises(ValueError, match="protocol_raw"):
        QoEResult(protocol=None, protocol_raw="h2c")
    with pytest.raises(TypeError):
        QoEResult(protocol=2)  # type: ignore[arg-type]
    result = QoEResult(protocol=HttpVersion.H2)
    with pytest.raises(ValueError, match="protocol_raw"):
        result.protocol_raw = "x"
    assert result.protocol is HttpVersion.H2


# --- MeasurementSpec (M21) ----------------------------------------------------------


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


# --- TrafficSpec (M23) --------------------------------------------------------------


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


# --- RADIUS (M24-M26, O34) ----------------------------------------------------------


def _record(**kw: object) -> RadiusAccountingRecord:
    base: dict[str, object] = {
        "timestamp": 1.0,
        "session_id": "s",
        "username": "u",
        "nas_address": "192.0.2.1",
        "record_type": AcctStatusType.STOP,
        "session_time": None,
        "input_octets": None,
        "output_octets": None,
        "input_packets": None,
        "output_packets": None,
        "terminate_cause": None,
    }
    base.update(kw)
    return RadiusAccountingRecord(**base)  # type: ignore[arg-type]


def test_accounting_record_type_released_words() -> None:
    for word in ("Start", "Interim-Update", "Stop"):
        with pytest.warns(DeprecationWarning, match="AcctStatusType"):
            assert _record(record_type=word).record_type == word
    with pytest.warns(DeprecationWarning):
        assert _record(record_type="Interim-Update").record_type is AcctStatusType.INTERIM_UPDATE


def test_acct_status_type_registry_values() -> None:
    assert [m.value for m in AcctStatusType][:5] == [
        "Start", "Stop", "Interim-Update", "Accounting-On", "Accounting-Off",
    ]  # fmt: skip
    for word in ("Tunnel-Start", "Tunnel-Link-Reject", "Failed"):
        assert AcctStatusType(word)


def test_acct_status_type_is_open_and_keeps_the_raw_word() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        record = _record(record_type="Vendor-Status")
    assert record.record_type is AcctStatusType.OTHER
    assert record.record_type_raw == "Vendor-Status"
    record.record_type = "start"  # case-sensitive: an unknown word, not a member: no warning
    assert (record.record_type, record.record_type_raw) == (AcctStatusType.OTHER, "start")
    record.record_type = AcctStatusType.STOP
    assert _equal(record.record_type_raw, None)
    changed = dataclasses.replace(_record(record_type="X1"), record_type="X2")
    assert (changed.record_type, changed.record_type_raw) == (AcctStatusType.OTHER, "X2")
    with pytest.raises(ValueError, match="record_type_raw"):
        _record(record_type=AcctStatusType.STOP, record_type_raw="x")


def test_acct_terminate_cause_is_a_pure_enum_with_the_registry() -> None:
    assert not issubclass(AcctTerminateCause, str)
    registered = [m for m in AcctTerminateCause if m is not AcctTerminateCause.OTHER]
    assert [m.code for m in registered] == list(range(1, 24))  # RFC 2866 1-18, RFC 3580 19-22, 23
    assert AcctTerminateCause.OTHER.code is None
    expected = {
        1: "User-Request", 4: "Idle-Timeout", 5: "Session-Timeout", 9: "NAS-Error",
        15: "Service-Unavailable", 18: "Host-Request", 19: "Supplicant-Restart",
        20: "Reauthentication-Failure", 21: "Port-Reinit", 22: "Port-Disabled", 23: "Lost-Power",
    }  # fmt: skip
    for code, word in expected.items():
        assert AcctTerminateCause(word).code == code


def test_terminate_cause_conversion() -> None:
    assert _record().terminate_cause is None
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        member = _record(terminate_cause=AcctTerminateCause.LOST_CARRIER).terminate_cause
    assert member is AcctTerminateCause.LOST_CARRIER
    with pytest.warns(DeprecationWarning, match="AcctTerminateCause.USER_REQUEST"):
        assert _record(terminate_cause="User-Request").terminate_cause is (
            AcctTerminateCause.USER_REQUEST
        )
    with pytest.warns(DeprecationWarning):  # the RFC's prose spelling
        assert _record(terminate_cause="Lost Carrier").terminate_cause is (
            AcctTerminateCause.LOST_CARRIER
        )
    with pytest.raises(TypeError):
        _record(terminate_cause=1)
    record = _record()
    record.terminate_cause = AcctTerminateCause.PORT_ERROR
    record.terminate_cause = None
    assert record.terminate_cause is None
    with pytest.warns(DeprecationWarning):
        record.terminate_cause = "Port Disabled"
    assert _equal(record.terminate_cause, AcctTerminateCause.PORT_DISABLED)


@pytest.mark.parametrize(
    ("prose", "member"),
    [
        ("User Request", AcctTerminateCause.USER_REQUEST),
        ("Lost Power", AcctTerminateCause.LOST_POWER),
        ("Port Reinitialized", AcctTerminateCause.PORT_REINIT),
        ("Port Administratively Disabled", AcctTerminateCause.PORT_DISABLED),
        ("Reauthentication Failure", AcctTerminateCause.REAUTHENTICATION_FAILURE),
    ],
)
def test_terminate_cause_prose_spellings_alias_and_warn_with_the_given_word(
    prose: str, member: AcctTerminateCause
) -> None:
    with pytest.warns(DeprecationWarning) as record:
        built = _record(terminate_cause=prose)
        built.terminate_cause = None
        built.terminate_cause = prose
    assert _equal(built.terminate_cause, member)
    assert built.terminate_cause_raw is None
    assert len(record) == 2
    for warning in record:
        assert repr(prose) in str(warning.message)
        assert f"AcctTerminateCause.{member.name}" in str(warning.message)
        assert warning.filename == __file__
    assert AcctTerminateCause(prose) is member  # the enum constructor takes the alias too


def test_terminate_cause_unlisted_prose_is_an_unknown_word() -> None:
    record = _record(terminate_cause="Port Disable")  # names no member in any spelling
    assert record.terminate_cause is AcctTerminateCause.OTHER
    assert record.terminate_cause_raw == "Port Disable"


def test_acct_status_type_codes_and_new_values() -> None:
    codes = {
        "Start": 1, "Stop": 2, "Interim-Update": 3, "Accounting-On": 7, "Accounting-Off": 8,
        "Tunnel-Start": 9, "Tunnel-Stop": 10, "Tunnel-Reject": 11, "Tunnel-Link-Start": 12,
        "Tunnel-Link-Stop": 13, "Tunnel-Link-Reject": 14, "Failed": 15,
        "Subsystem-On": 18, "Subsystem-Off": 19,
    }  # fmt: skip
    for word, code in codes.items():
        assert AcctStatusType(word).code == code
    assert AcctStatusType.OTHER.code is None
    assert {m.value for m in AcctStatusType} == {*codes, "other"}


def test_terminate_cause_is_open_and_keeps_the_raw_word() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        record = _record(terminate_cause="Vendor-Cause")
    assert record.terminate_cause is AcctTerminateCause.OTHER
    assert record.terminate_cause_raw == "Vendor-Cause"
    assert _record().terminate_cause_raw is None
    with pytest.raises(ValueError, match="terminate_cause_raw"):
        _record(terminate_cause=None, terminate_cause_raw="x")
    both = dataclasses.replace(record, record_type=AcctStatusType.START)
    assert both.terminate_cause_raw == "Vendor-Cause"  # the other pair is unchanged


def test_radius_user_eap_methods_open_set() -> None:
    with pytest.warns(DeprecationWarning, match="eap_methods_known"):
        user = RadiusUser("alice", eap_methods=["PEAP-MSCHAPv2", "TTLS-PAP"])
    assert user.eap_methods_known == (EapMethod.PEAP_MSCHAPV2, EapMethod.TTLS_PAP)
    assert user.eap_methods_unknown == ()
    with pytest.warns(DeprecationWarning):
        vendor = RadiusUser("bob", eap_methods=["PEAP-MSCHAPv2", "EAP-VENDOR"])
    assert vendor.eap_methods_known == (EapMethod.PEAP_MSCHAPV2,)
    assert vendor.eap_methods_unknown == ("EAP-VENDOR",)
    assert vendor.eap_methods == ["PEAP-MSCHAPv2", "EAP-VENDOR"]


def test_radius_user_typed_side_fills_the_word_list_silently() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        user = RadiusUser(
            "carol", eap_methods_known=(EapMethod.TLS,), eap_methods_unknown=("EAP-VENDOR",)
        )
        assert user.eap_methods == ["EAP-TLS", "EAP-VENDOR"]
        assert RadiusUser("dave").eap_methods == []
        user.eap_methods_known = (EapMethod.AKA,)
    assert user.eap_methods == ["EAP-AKA", "EAP-VENDOR"]
    with pytest.warns(DeprecationWarning):
        user.eap_methods = ["EAP-SIM"]
    assert user.eap_methods_known == (EapMethod.SIM,)
    assert user.eap_methods_unknown == ()


def test_radius_user_refusals() -> None:
    with pytest.raises(ValueError, match="disagree"):
        RadiusUser("e", eap_methods=["EAP-TLS"], eap_methods_known=(EapMethod.SIM,))
    with pytest.raises(TypeError):
        RadiusUser("e", eap_methods_known="EAP-TLS")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="belongs in"):
        RadiusUser("e", eap_methods_unknown=("EAP-TLS",))
    user = RadiusUser("f", eap_methods_known=(EapMethod.TLS,))
    with pytest.raises(TypeError):
        user.eap_methods_known = ("EAP-TLS",)  # type: ignore[assignment]
    assert user.eap_methods == ["EAP-TLS"]


# --- StormControlConfig (M33) -------------------------------------------------------


def test_storm_control_unit_is_an_addition() -> None:
    config = StormControlConfig("1", {StormControlType.BROADCAST: 10.0})
    assert config.unit is None
    assert StormControlConfig("1", unit=StormControlUnit.PPS).unit is StormControlUnit.PPS
    assert [f.name for f in dataclasses.fields(StormControlConfig)] == [
        "port",
        "thresholds",
        "unit",
    ]
