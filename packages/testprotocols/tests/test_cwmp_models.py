"""CWMP structures for the typed TR-069 RPCs (``testprotocols.models.cwmp``)."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta, timezone

import pytest
from testprotocols.models import (
    AddObjectResult,
    CwmpFileType,
    CwmpNotification,
    CwmpStatus,
    CwmpType,
    DownloadResult,
    ParameterAttribute,
    ParameterInfo,
    ParameterValue,
)

_NAME = "Device.DeviceInfo.UpTime"

# One value per CWMP type, with its XML Schema lexical form (the text on the wire).
_ONE_OF_EACH: list[tuple[CwmpType, object, str]] = [
    (CwmpType.STRING, "prplOS-4.0.3", "prplOS-4.0.3"),
    (CwmpType.STRING, "", ""),
    (CwmpType.INT, -2147483648, "-2147483648"),
    (CwmpType.INT, 2147483647, "2147483647"),
    (CwmpType.UNSIGNED_INT, 4294967295, "4294967295"),
    (CwmpType.UNSIGNED_INT, 0, "0"),
    (CwmpType.LONG, -9223372036854775808, "-9223372036854775808"),
    (CwmpType.UNSIGNED_LONG, 18446744073709551615, "18446744073709551615"),
    (CwmpType.BOOLEAN, True, "true"),
    (CwmpType.BOOLEAN, False, "false"),
    (
        CwmpType.DATE_TIME,
        datetime(2026, 10, 4, 12, 30, 5, tzinfo=UTC),
        "2026-10-04T12:30:05Z",
    ),
    (
        CwmpType.DATE_TIME,
        datetime(2026, 10, 4, 12, 30, 5, 250000, tzinfo=timezone(timedelta(hours=2))),
        "2026-10-04T12:30:05.250000+02:00",
    ),
    (CwmpType.DATE_TIME, datetime(1, 1, 1, tzinfo=UTC), "0001-01-01T00:00:00Z"),
    (CwmpType.DATE_TIME, datetime(2026, 10, 4, 12, 30, 5), "2026-10-04T12:30:05"),
    (CwmpType.BASE64, b"\x00\xffcwmp", "AP9jd21w"),
    (CwmpType.HEX_BINARY, b"\x00\xab\x10", "00AB10"),
]


def test_cwmp_type_values_are_the_xsd_type_names() -> None:
    assert [t.value for t in CwmpType] == [
        "xsd:string",
        "xsd:int",
        "xsd:unsignedInt",
        "xsd:long",
        "xsd:unsignedLong",
        "xsd:boolean",
        "xsd:dateTime",
        "xsd:base64",
        "xsd:hexBinary",
    ]


@pytest.mark.parametrize(("cwmp_type", "value", "text"), _ONE_OF_EACH)
def test_parameter_value_round_trips_each_cwmp_type(
    cwmp_type: CwmpType, value: object, text: str
) -> None:
    pv = ParameterValue(_NAME, value, cwmp_type)  # type: ignore[arg-type]
    assert pv.text == text
    back = ParameterValue.from_text(_NAME, text, cwmp_type)
    assert back == pv
    assert type(back.value) is type(pv.value)
    assert back.text == text


def test_every_cwmp_type_is_covered_by_the_round_trip() -> None:
    assert {t for t, _, _ in _ONE_OF_EACH} == set(CwmpType)


@pytest.mark.parametrize(
    ("cwmp_type", "text", "value"),
    [
        (CwmpType.BOOLEAN, "1", True),
        (CwmpType.BOOLEAN, "0", False),
        (CwmpType.INT, "+7", 7),
        (CwmpType.HEX_BINARY, "00ab10", b"\x00\xab\x10"),
        (CwmpType.DATE_TIME, "2026-10-04T12:30:05.1234567Z", None),
    ],
)
def test_from_text_reads_the_other_xsd_spellings(
    cwmp_type: CwmpType, text: str, value: object
) -> None:
    pv = ParameterValue.from_text(_NAME, text, cwmp_type)
    if value is not None:
        assert pv.value == value
    else:
        assert pv.value == datetime(2026, 10, 4, 12, 30, 5, 123456, tzinfo=UTC)


@pytest.mark.parametrize(
    ("cwmp_type", "value"),
    [
        (CwmpType.STRING, 5),
        (CwmpType.INT, "5"),
        (CwmpType.INT, True),
        (CwmpType.INT, 1.5),
        (CwmpType.UNSIGNED_INT, False),
        (CwmpType.LONG, "1"),
        (CwmpType.UNSIGNED_LONG, 2.0),
        (CwmpType.BOOLEAN, 1),
        (CwmpType.BOOLEAN, "true"),
        (CwmpType.DATE_TIME, "2026-10-04T12:30:05Z"),
        (CwmpType.BASE64, "AP9jd21w"),
        (CwmpType.HEX_BINARY, "00AB10"),
        (CwmpType.BASE64, bytearray(b"x")),
    ],
)
def test_parameter_value_refuses_a_mismatched_value(cwmp_type: CwmpType, value: object) -> None:
    with pytest.raises(TypeError, match=r"ParameterValue\.value"):
        ParameterValue(_NAME, value, cwmp_type)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("cwmp_type", "value"),
    [
        (CwmpType.INT, 2147483648),
        (CwmpType.INT, -2147483649),
        (CwmpType.UNSIGNED_INT, -1),
        (CwmpType.UNSIGNED_INT, 4294967296),
        (CwmpType.LONG, 9223372036854775808),
        (CwmpType.UNSIGNED_LONG, -1),
        (CwmpType.UNSIGNED_LONG, 18446744073709551616),
    ],
)
def test_parameter_value_refuses_an_out_of_range_number(cwmp_type: CwmpType, value: int) -> None:
    with pytest.raises(ValueError, match=r"ParameterValue\.value"):
        ParameterValue(_NAME, value, cwmp_type)


@pytest.mark.parametrize(
    ("cwmp_type", "text"),
    [
        (CwmpType.INT, "1_000"),
        (CwmpType.INT, " 5"),
        (CwmpType.INT, "0x10"),
        (CwmpType.BOOLEAN, "yes"),
        (CwmpType.BOOLEAN, "True"),
        (CwmpType.DATE_TIME, "2026-10-04"),
        (CwmpType.DATE_TIME, "20261004T123005Z"),
        (CwmpType.BASE64, "not base64!"),
        (CwmpType.HEX_BINARY, "0AB"),
        (CwmpType.HEX_BINARY, "00 AB"),
    ],
)
def test_from_text_refuses_malformed_text(cwmp_type: CwmpType, text: str) -> None:
    with pytest.raises(ValueError, match="not an xsd"):
        ParameterValue.from_text(_NAME, text, cwmp_type)


def test_from_text_checks_the_range_too() -> None:
    with pytest.raises(ValueError, match="must be 0 to 4294967295"):
        ParameterValue.from_text(_NAME, "-1", CwmpType.UNSIGNED_INT)


def test_parameter_value_refuses_a_plain_string_type_and_an_empty_name() -> None:
    with pytest.raises(TypeError, match="CwmpType"):
        ParameterValue(_NAME, "x", "xsd:string")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="name"):
        ParameterValue("", "x", CwmpType.STRING)
    with pytest.raises(TypeError, match="name"):
        ParameterValue(None, "x", CwmpType.STRING)  # type: ignore[arg-type]


def test_parameter_value_is_frozen_and_validates_replace() -> None:
    pv = ParameterValue(_NAME, 5, CwmpType.UNSIGNED_INT)
    with pytest.raises(dataclasses.FrozenInstanceError):
        pv.value = 6  # type: ignore[misc]
    with pytest.raises(TypeError):
        dataclasses.replace(pv, type=CwmpType.BOOLEAN)


def test_the_vitro_bdd_genieacs_output_maps_onto_parameter_value() -> None:
    # The vitro-bdd example ACS (GenieacsTr069Server.GPV) returns, for the recorded GenieACS
    # device leaf {"_value": "SN42", "_type": "xsd:string"}, this released entry:
    released = {"key": "Device.DeviceInfo.SerialNumber", "value": "SN42", "type": "xsd:string"}
    pv = ParameterValue(released["key"], released["value"], CwmpType(released["type"]))
    assert pv == ParameterValue("Device.DeviceInfo.SerialNumber", "SN42", CwmpType.STRING)
    assert (pv.name, pv.value, pv.type.value) == (
        released["key"],
        released["value"],
        released["type"],
    )


def test_cwmp_notification_values() -> None:
    assert [(n.name, int(n)) for n in CwmpNotification] == [
        ("OFF", 0),
        ("PASSIVE", 1),
        ("ACTIVE", 2),
        ("PASSIVE_LIGHTWEIGHT", 3),
        ("PASSIVE_AND_PASSIVE_LIGHTWEIGHT", 4),
        ("ACTIVE_LIGHTWEIGHT", 5),
        ("PASSIVE_AND_ACTIVE_LIGHTWEIGHT", 6),
    ]


def test_parameter_attribute_checks_its_fields() -> None:
    attr = ParameterAttribute(_NAME, CwmpNotification.ACTIVE, ["Subscriber"])  # type: ignore[arg-type]
    assert attr.access_list == ("Subscriber",)
    assert ParameterAttribute(_NAME, CwmpNotification.OFF).access_list == ()
    with pytest.raises(TypeError, match="notification"):
        ParameterAttribute(_NAME, 2)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="access_list"):
        ParameterAttribute(_NAME, CwmpNotification.OFF, "Subscriber")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="name"):
        ParameterAttribute("", CwmpNotification.OFF)


def test_parameter_info_checks_its_fields() -> None:
    assert ParameterInfo("Device.DeviceInfo.", False).writable is False
    with pytest.raises(TypeError, match="writable"):
        ParameterInfo(_NAME, "false")  # type: ignore[arg-type]


def test_cwmp_status_and_file_type_values() -> None:
    assert [(s.name, int(s)) for s in CwmpStatus] == [("APPLIED", 0), ("NOT_YET_APPLIED", 1)]
    assert [f.value for f in CwmpFileType] == [
        "1 Firmware Upgrade Image",
        "2 Web Content",
        "3 Vendor Configuration File",
        "4 Tone File",
        "5 Ringer File",
        "6 Stored Firmware Image",
    ]


def test_add_object_result_checks_its_fields() -> None:
    assert AddObjectResult(3, CwmpStatus.APPLIED).instance_number == 3
    with pytest.raises(ValueError, match="instance_number"):
        AddObjectResult(0, CwmpStatus.APPLIED)
    with pytest.raises(TypeError, match="instance_number"):
        AddObjectResult(True, CwmpStatus.APPLIED)
    with pytest.raises(TypeError, match="status"):
        AddObjectResult(1, 0)  # type: ignore[arg-type]


def test_download_result_checks_its_fields() -> None:
    start = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
    done = DownloadResult(CwmpStatus.APPLIED, start, start + timedelta(seconds=30))
    assert done.complete_time == start + timedelta(seconds=30)
    assert DownloadResult(CwmpStatus.NOT_YET_APPLIED).start_time is None
    with pytest.raises(ValueError, match="not yet applied"):
        DownloadResult(CwmpStatus.NOT_YET_APPLIED, start, start)
    with pytest.raises(ValueError, match="before"):
        DownloadResult(CwmpStatus.APPLIED, start, start - timedelta(seconds=1))
    with pytest.raises(TypeError, match="start_time"):
        DownloadResult(CwmpStatus.APPLIED, "2026-10-04T12:00:00Z")  # type: ignore[arg-type]
