"""CWMP (TR-069) structures carried by the typed ``Tr069Server`` RPCs.

The records follow the CWMP schema (Broadband Forum ``cwmp-1-2.xsd`` and
``cwmp-1-4.xsd``) and the parameter data types of TR-106 ("Data Model Template for
TR-069-Enabled Devices", section 3.2 "Data Types"):

- ``ParameterValue`` is a ``ParameterValueStruct`` (GetParameterValues,
  SetParameterValues): a name, a value and its ``xsi:type``.
- ``ParameterAttribute`` is a ``ParameterAttributeStruct`` (GetParameterAttributes) and the
  attribute part of a ``SetParameterAttributesStruct``.
- ``ParameterInfo`` is a ``ParameterInfoStruct`` (GetParameterNames).
- ``AddObjectResult`` and ``DownloadResult`` are the AddObject and Download responses;
  ``CwmpStatus`` is the ``Status`` of the SetParameterValues, AddObject, DeleteObject and
  Download responses.
- ``CwmpFileType`` is the Download ``FileType``.

A ``ParameterValue`` checks that its value matches its type; ``ParameterValue.from_text``
and ``ParameterValue.text`` convert to and from the XML Schema lexical form a CWMP message
carries.
"""

from __future__ import annotations

import base64
import binascii
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum, IntEnum, StrEnum

from testprotocols.models import _checks


class CwmpType(StrEnum):
    """A CWMP parameter data type (TR-106 section 3.2), as its ``xsi:type`` name."""

    STRING = "xsd:string"
    INT = "xsd:int"
    UNSIGNED_INT = "xsd:unsignedInt"
    LONG = "xsd:long"
    UNSIGNED_LONG = "xsd:unsignedLong"
    BOOLEAN = "xsd:boolean"
    DATE_TIME = "xsd:dateTime"
    BASE64 = "xsd:base64"
    HEX_BINARY = "xsd:hexBinary"


CwmpValue = str | int | bool | datetime | bytes
"""A CWMP parameter value: ``str`` (string), ``int`` (int, unsignedInt, long, unsignedLong),
``bool`` (boolean), ``datetime`` (dateTime) or ``bytes`` (base64, hexBinary)."""

_INT_RANGES: dict[CwmpType, tuple[int, int]] = {
    CwmpType.INT: (-(2**31), 2**31 - 1),
    CwmpType.UNSIGNED_INT: (0, 2**32 - 1),
    CwmpType.LONG: (-(2**63), 2**63 - 1),
    CwmpType.UNSIGNED_LONG: (0, 2**64 - 1),
}
_PYTHON_TYPES: dict[CwmpType, type] = {
    CwmpType.STRING: str,
    CwmpType.BOOLEAN: bool,
    CwmpType.DATE_TIME: datetime,
    CwmpType.BASE64: bytes,
    CwmpType.HEX_BINARY: bytes,
}
_INTEGER = re.compile(r"[+-]?[0-9]+")
_DATE_TIME = re.compile(
    r"(?P<main>[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})"
    r"(?:\.(?P<fraction>[0-9]+))?(?P<zone>Z|[+-][0-9]{2}:[0-9]{2})?"
)
_BASE64 = re.compile(r"(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?")
_HEX = re.compile(r"(?:[0-9A-Fa-f]{2})*")
_BOOLEANS = {"true": True, "1": True, "false": False, "0": False}


def _check_member(owner: str, name: str, value: object, enum_type: type[Enum]) -> None:
    """Raise ``TypeError`` unless *value* is a member of *enum_type* (a plain ``str`` or
    ``int`` is refused: ``enum_type(value)`` converts one)."""
    if not isinstance(value, enum_type):
        raise TypeError(
            f"{owner}.{name} takes a {enum_type.__name__} ({enum_type.__name__}({value!r})), "
            f"not {value!r}"
        )


def _check_value(value: object, cwmp_type: CwmpType) -> None:
    """Raise ``TypeError`` or ``ValueError`` unless *value* is a legal *cwmp_type* value."""
    where = "ParameterValue.value"
    if cwmp_type in _INT_RANGES:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{where} of type {cwmp_type} takes an int, not {value!r}")
        low, high = _INT_RANGES[cwmp_type]
        if not low <= value <= high:
            raise ValueError(f"{where} of type {cwmp_type} must be {low} to {high}: {value}")
        return
    expected = _PYTHON_TYPES[cwmp_type]
    if not isinstance(value, expected):
        raise TypeError(f"{where} of type {cwmp_type} takes a {expected.__name__}, not {value!r}")


def _format_date_time(value: datetime) -> str:
    text = value.isoformat()
    offset = value.utcoffset()
    if offset is not None and offset == timedelta(0):
        text = text[: -len("+00:00")] + "Z"
    return text


def _parse_date_time(text: str) -> datetime:
    match = _DATE_TIME.fullmatch(text)
    if match is None:
        raise ValueError
    fraction = match["fraction"]
    zone = match["zone"]
    normal = match["main"]
    if fraction:
        normal += "." + fraction[:6].ljust(6, "0")
    if zone == "Z":
        normal += "+00:00"
    elif zone:
        normal += zone
    parsed = datetime.fromisoformat(normal)
    return parsed.replace(tzinfo=UTC) if zone == "Z" else parsed


def _parse(text: str, cwmp_type: CwmpType) -> CwmpValue:
    """The *cwmp_type* value of the lexical form *text*; ``ValueError`` when malformed."""
    if cwmp_type is CwmpType.STRING:
        return text
    if cwmp_type in _INT_RANGES:
        if _INTEGER.fullmatch(text) is None:
            raise ValueError
        return int(text)
    if cwmp_type is CwmpType.BOOLEAN:
        return _BOOLEANS[text]
    if cwmp_type is CwmpType.DATE_TIME:
        return _parse_date_time(text)
    if cwmp_type is CwmpType.BASE64:
        if _BASE64.fullmatch(text) is None:
            raise ValueError
        return base64.b64decode(text, validate=True)
    if _HEX.fullmatch(text) is None:
        raise ValueError
    return binascii.unhexlify(text)


@dataclass(frozen=True)
class ParameterValue:
    """A ``ParameterValueStruct``: a parameter's full *name*, its *value* and its *type*.

    *value* must match *type*: ``str`` for ``STRING``; an ``int`` (never a ``bool``) within
    the type's range for ``INT`` (32-bit signed), ``UNSIGNED_INT`` (0 to 2**32 - 1),
    ``LONG`` (64-bit signed) and ``UNSIGNED_LONG`` (0 to 2**64 - 1); ``bool`` for
    ``BOOLEAN``; ``datetime`` for ``DATE_TIME`` (the CWMP unknown time is
    ``0001-01-01T00:00:00Z``); ``bytes`` for ``BASE64`` and ``HEX_BINARY``. A value of the
    wrong Python type raises ``TypeError``; a number out of range raises ``ValueError``.
    """

    name: str
    value: CwmpValue
    type: CwmpType

    def __post_init__(self) -> None:
        _checks.text("ParameterValue", "name", self.name)
        if not self.name:
            raise ValueError("ParameterValue.name cannot be empty")
        _check_member("ParameterValue", "type", self.type, CwmpType)
        _check_value(self.value, self.type)

    @classmethod
    def from_text(cls, name: str, text: str, type: CwmpType) -> ParameterValue:
        """The value whose XML Schema lexical form is *text*, as a CWMP message carries it.

        Reads the canonical forms ``text`` writes and the other forms XML Schema allows:
        ``1``/``0`` for a boolean, a leading ``+`` on a number, lower-case hex digits, and
        more than six fraction digits on a dateTime (cut to microseconds). Malformed text
        raises ``ValueError``.
        """
        _check_member("ParameterValue", "type", type, CwmpType)
        _checks.text("ParameterValue", "text", text)
        try:
            value = _parse(text, type)
        except (ValueError, KeyError, binascii.Error):
            raise ValueError(f"{text!r} is not an {type} value") from None
        return cls(name, value, type)

    @property
    def text(self) -> str:
        """The value's canonical XML Schema lexical form: ``true``/``false`` for a
        boolean, decimal digits for a number, ISO 8601 for a dateTime (``Z`` for UTC, no
        zone for a naive ``datetime``), standard base64, upper-case hex."""
        value = self.value
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, datetime):
            return _format_date_time(value)
        if isinstance(value, bytes):
            if self.type is CwmpType.BASE64:
                return base64.b64encode(value).decode("ascii")
            return value.hex().upper()
        return str(value)


class CwmpNotification(IntEnum):
    """A parameter's ``Notification`` attribute (cwmp-1-4, values 0 to 6)."""

    OFF = 0
    PASSIVE = 1
    ACTIVE = 2
    PASSIVE_LIGHTWEIGHT = 3
    PASSIVE_AND_PASSIVE_LIGHTWEIGHT = 4
    ACTIVE_LIGHTWEIGHT = 5
    PASSIVE_AND_ACTIVE_LIGHTWEIGHT = 6


@dataclass(frozen=True)
class ParameterAttribute:
    """A ``ParameterAttributeStruct``: a parameter's *notification* and *access_list*.

    *access_list* names the entities, besides the ACS, that may write the parameter
    (``"Subscriber"`` is the one the schema defines); a list is stored as a tuple, a single
    ``str`` is refused.
    """

    name: str
    notification: CwmpNotification
    access_list: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _checks.text("ParameterAttribute", "name", self.name)
        if not self.name:
            raise ValueError("ParameterAttribute.name cannot be empty")
        _check_member("ParameterAttribute", "notification", self.notification, CwmpNotification)
        held = _checks.texts("ParameterAttribute", "access_list", self.access_list)
        object.__setattr__(self, "access_list", held)


@dataclass(frozen=True)
class ParameterInfo:
    """A ``ParameterInfoStruct``: a parameter or object *name* (an object's ends with
    ``.``) and whether the ACS may write it."""

    name: str
    writable: bool

    def __post_init__(self) -> None:
        _checks.text("ParameterInfo", "name", self.name)
        _checks.flag("ParameterInfo", "writable", self.writable)


class CwmpStatus(IntEnum):
    """The ``Status`` of a SetParameterValues, AddObject, DeleteObject or Download response.

    ``APPLIED`` (0): the change has been validated and applied. ``NOT_YET_APPLIED`` (1): it
    has been validated and committed but is not applied yet (for example until a reboot);
    for a Download, the download has not completed and been applied yet.
    """

    APPLIED = 0
    NOT_YET_APPLIED = 1


def _check_status(owner: str, value: object) -> None:
    _check_member(owner, "status", value, CwmpStatus)


@dataclass(frozen=True)
class AddObjectResult:
    """An AddObject response: the new instance's *instance_number* (1 or more) and the
    *status*."""

    instance_number: int
    status: CwmpStatus

    def __post_init__(self) -> None:
        _checks.count("AddObjectResult", "instance_number", self.instance_number)
        if self.instance_number < 1:
            raise ValueError(
                f"AddObjectResult.instance_number must be 1 or more: {self.instance_number}"
            )
        _check_status("AddObjectResult", self.status)


@dataclass(frozen=True)
class DownloadResult:
    """A Download response: the *status*, and when the transfer started and completed.

    The times are ``None`` when unknown (the CWMP unknown time); they are always ``None``
    while the status is ``NOT_YET_APPLIED``.
    """

    status: CwmpStatus
    start_time: datetime | None = None
    complete_time: datetime | None = None

    def __post_init__(self) -> None:
        _check_status("DownloadResult", self.status)
        for name in ("start_time", "complete_time"):
            value: object = getattr(self, name)
            if value is not None:
                _checks.when("DownloadResult", name, value)
        timed = self.start_time is not None or self.complete_time is not None
        if self.status is CwmpStatus.NOT_YET_APPLIED and timed:
            raise ValueError("DownloadResult times are unknown while the status is not yet applied")
        if (
            self.start_time is not None
            and self.complete_time is not None
            and self.complete_time < self.start_time
        ):
            raise ValueError("DownloadResult.complete_time is before start_time")


class CwmpFileType(StrEnum):
    """A Download ``FileType``: the standard file types, numbered as on the wire."""

    FIRMWARE_UPGRADE_IMAGE = "1 Firmware Upgrade Image"
    WEB_CONTENT = "2 Web Content"
    VENDOR_CONFIGURATION_FILE = "3 Vendor Configuration File"
    TONE_FILE = "4 Tone File"
    RINGER_FILE = "5 Ringer File"
    STORED_FIRMWARE_IMAGE = "6 Stored Firmware Image"
