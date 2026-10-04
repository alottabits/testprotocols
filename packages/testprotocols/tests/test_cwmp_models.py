"""CWMP structures for the typed TR-069 RPCs (``testprotocols.models.cwmp``)."""

from __future__ import annotations

import dataclasses
import warnings
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

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
    (CwmpType.DECIMAL, Decimal("-12.50"), "-12.50"),
    (CwmpType.DECIMAL, Decimal("100"), "100"),
    (CwmpType.DECIMAL, Decimal("1E+2"), "100"),
    (CwmpType.OTHER, "opaque 42", "opaque 42"),
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
        "xsd:decimal",
        "other",
    ]


@pytest.mark.parametrize(("cwmp_type", "value", "text"), _ONE_OF_EACH)
def test_parameter_value_round_trips_each_cwmp_type(
    cwmp_type: CwmpType, value: object, text: str
) -> None:
    raw = "xsd:duration" if cwmp_type is CwmpType.OTHER else None
    pv = ParameterValue(_NAME, value, cwmp_type, raw)  # type: ignore[arg-type]
    assert pv.text == text
    back = ParameterValue.from_text(_NAME, text, raw if raw is not None else cwmp_type)
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
        (CwmpType.DECIMAL, 1),
        (CwmpType.DECIMAL, 1.5),
        (CwmpType.DECIMAL, "1.5"),
        (CwmpType.OTHER, 5),
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
        (CwmpType.DECIMAL, "1e5"),
        (CwmpType.DECIMAL, "NaN"),
        (CwmpType.DECIMAL, "1,5"),
    ],
)
def test_from_text_refuses_malformed_text(cwmp_type: CwmpType, text: str) -> None:
    with pytest.raises(ValueError, match="not an xsd"):
        ParameterValue.from_text(_NAME, text, cwmp_type)


def test_from_text_checks_the_range_too() -> None:
    with pytest.raises(ValueError, match="must be 0 to 4294967295"):
        ParameterValue.from_text(_NAME, "-1", CwmpType.UNSIGNED_INT)


def test_parameter_value_refuses_an_empty_name() -> None:
    with pytest.raises(ValueError, match="name"):
        ParameterValue("", "x", CwmpType.STRING)
    with pytest.raises(TypeError, match="name"):
        ParameterValue(None, "x", CwmpType.STRING)  # type: ignore[arg-type]


def test_decimal_values() -> None:
    assert ParameterValue(_NAME, Decimal("0.1"), CwmpType.DECIMAL).text == "0.1"
    assert ParameterValue.from_text(_NAME, ".5", CwmpType.DECIMAL).value == Decimal("0.5")
    assert ParameterValue.from_text(_NAME, "+3.", CwmpType.DECIMAL).value == Decimal("3")
    for bad in (Decimal("NaN"), Decimal("Infinity")):
        with pytest.raises(ValueError, match="finite"):
            ParameterValue(_NAME, bad, CwmpType.DECIMAL)


def test_an_unknown_type_is_other_with_the_raw_word_and_a_text_value() -> None:
    pv = ParameterValue(_NAME, "P1DT2H", "xsd:duration")  # type: ignore[arg-type]
    assert (pv.type, pv.type_raw) == (CwmpType.OTHER, "xsd:duration")
    assert pv == ParameterValue(_NAME, "P1DT2H", CwmpType.OTHER, "xsd:duration")
    read = ParameterValue.from_text(_NAME, "P1DT2H", "xsd:duration")
    assert (read.type, read.type_raw, read.value) == (CwmpType.OTHER, "xsd:duration", "P1DT2H")
    with pytest.raises(TypeError, match="takes a str"):
        ParameterValue(_NAME, 5, CwmpType.OTHER, "xsd:duration")


def test_a_missing_type_is_other_with_no_raw_word() -> None:
    pv = ParameterValue(_NAME, "42", CwmpType.OTHER)
    assert (pv.type, pv.type_raw) == (CwmpType.OTHER, None)
    read = ParameterValue.from_text(_NAME, "42", None)
    assert (read.type, read.type_raw, read.value) == (CwmpType.OTHER, None, "42")


def test_a_raw_word_with_a_named_type_is_refused() -> None:
    with pytest.raises(ValueError, match="type_raw"):
        ParameterValue(_NAME, "x", CwmpType.STRING, "xsd:string")


def test_from_text_takes_the_device_word_without_a_warning() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        pv = ParameterValue.from_text(_NAME, "7", "xsd:unsignedInt")
    assert (pv.type, pv.type_raw, pv.value) == (CwmpType.UNSIGNED_INT, None, 7)


@pytest.mark.parametrize("word", ["xsd:base64", "xsd:base64Binary", "soapenc:base64"])
def test_the_base64_spellings_are_one_type(word: str) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        read = ParameterValue.from_text(_NAME, "AP8=", word)
        built = ParameterValue(_NAME, b"\x00\xff", CwmpType(word))
    assert (read.type, read.type_raw, read.value) == (CwmpType.BASE64, None, b"\x00\xff")
    assert built == read


def test_a_plain_string_naming_a_member_converts_and_warns() -> None:
    with pytest.warns(DeprecationWarning, match="CwmpType.STRING"):
        pv = ParameterValue(_NAME, "x", "xsd:string")  # type: ignore[arg-type]
    assert (pv.type, pv.type_raw) == (CwmpType.STRING, None)


def test_a_wrong_kind_of_type_is_refused() -> None:
    with pytest.raises(TypeError):
        ParameterValue(_NAME, "x", 5)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ParameterValue(_NAME, "x", None)  # type: ignore[arg-type]


def test_parameter_value_is_frozen_and_validates_replace() -> None:
    pv = ParameterValue(_NAME, 5, CwmpType.UNSIGNED_INT)
    with pytest.raises(dataclasses.FrozenInstanceError):
        pv.value = 6  # type: ignore[misc]
    with pytest.raises(TypeError):
        dataclasses.replace(pv, type=CwmpType.BOOLEAN)
    other = ParameterValue(_NAME, "P1D", CwmpType.OTHER, "xsd:duration")
    # the side that changed wins: a new type drops the old raw word
    assert dataclasses.replace(other, type=CwmpType.STRING).type_raw is None
    assert dataclasses.replace(other, type_raw="xsd:gYear").type is CwmpType.OTHER


@pytest.mark.parametrize("seconds", [30, -30, 3601])
def test_a_date_time_offset_must_be_whole_minutes(seconds: int) -> None:
    zone = timezone(timedelta(seconds=seconds))
    with pytest.raises(ValueError, match="whole minutes"):
        ParameterValue(_NAME, datetime(2026, 10, 4, tzinfo=zone), CwmpType.DATE_TIME)


def test_every_date_time_text_reads_back() -> None:
    for zone in (None, UTC, timezone(timedelta(hours=-5, minutes=-30))):
        for micro in (0, 1, 500000):
            value = datetime(2026, 10, 4, 1, 2, 3, micro, tzinfo=zone)
            pv = ParameterValue(_NAME, value, CwmpType.DATE_TIME)
            assert ParameterValue.from_text(_NAME, pv.text, CwmpType.DATE_TIME) == pv


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
