"""CWMP (TR-069) structures carried by the typed ``Tr069Server`` RPCs.

The records follow the CWMP schema (Broadband Forum ``cwmp-1-2.xsd`` and
``cwmp-1-4.xsd``) and the built-in parameter data types of TR-106 Amendment 9 (data
model schema ``cwmp-datamodel-1-8.xsd``, ``AllBuiltinDataTypes``: base64, boolean,
dateTime, decimal, hexBinary, int, long, string, unsignedInt, unsignedLong):

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
carries. The type is open: a type word the device reports that names no built-in type, or
no type at all, is ``CwmpType.OTHER`` with the value kept as text, so nothing is lost or
guessed.
"""

from __future__ import annotations

import base64
import binascii
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import Enum, IntEnum, StrEnum
from typing import cast, override

from testprotocols.models import _checks
from testprotocols.models._open_enum import OpenEnumPair
from testprotocols.models._sync import settle


class CwmpType(StrEnum):
    """A CWMP parameter data type, as its ``xsi:type`` name; the set is open.

    The members are the built-in types of TR-106 Amendment 9 (``cwmp-datamodel-1-8.xsd``,
    ``AllBuiltinDataTypes``) and ``OTHER``, for a type word that names none of them (or a
    value reported with no type). ``BASE64`` is spelled ``xsd:base64``, as ACSs report it;
    ``CwmpType("xsd:base64Binary")`` (the XML Schema name) and
    ``CwmpType("soapenc:base64")`` (the spelling of ``cwmp-1-2.xsd``) give it too.
    """

    STRING = "xsd:string"
    INT = "xsd:int"
    UNSIGNED_INT = "xsd:unsignedInt"
    LONG = "xsd:long"
    UNSIGNED_LONG = "xsd:unsignedLong"
    BOOLEAN = "xsd:boolean"
    DATE_TIME = "xsd:dateTime"
    BASE64 = "xsd:base64"
    HEX_BINARY = "xsd:hexBinary"
    DECIMAL = "xsd:decimal"
    OTHER = "other"

    @override
    @classmethod
    def _missing_(cls, value: object) -> CwmpType | None:
        return _TYPE_ALIASES.get(value) if isinstance(value, str) else None


_TYPE_ALIASES: dict[str, CwmpType] = {
    "xsd:base64Binary": CwmpType.BASE64,
    "soapenc:base64": CwmpType.BASE64,
}


CwmpValue = str | int | bool | datetime | bytes | Decimal
"""A CWMP parameter value: ``str`` (string, and any ``OTHER`` type), ``int`` (int,
unsignedInt, long, unsignedLong), ``bool`` (boolean), ``datetime`` (dateTime), ``bytes``
(base64, hexBinary) or ``Decimal`` (decimal)."""

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
    CwmpType.DECIMAL: Decimal,
    CwmpType.OTHER: str,
}
_MAX_OFFSET = timedelta(hours=14)
_INTEGER = re.compile(r"[+-]?[0-9]+")
_DATE_TIME = re.compile(
    r"(?P<main>[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})"
    r"(?:\.(?P<fraction>[0-9]+))?(?P<zone>Z|[+-][0-9]{2}:[0-9]{2})?"
)
_BASE64 = re.compile(r"(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?")
_HEX = re.compile(r"(?:[0-9A-Fa-f]{2})*")
_DECIMAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)")
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
    if isinstance(value, Decimal) and not value.is_finite():
        raise ValueError(f"{where} of type {cwmp_type} must be finite: {value}")
    if isinstance(value, datetime):
        offset = value.utcoffset()
        if offset is not None and (offset % timedelta(minutes=1) or abs(offset) > _MAX_OFFSET):
            raise ValueError(
                f"{where} of type {cwmp_type}: a time zone offset is whole minutes, at most "
                f"14:00 (XML Schema dateTime), not {offset}"
            )


def _type_of(word: CwmpType | str | None) -> tuple[CwmpType, str | None]:
    """The type a device reports as *word*, and its raw word when it names no member."""
    given = cast(object, word)  # checked at run time too: callers are not all type-checked
    if isinstance(given, CwmpType):
        return given, None
    if given is None:
        return CwmpType.OTHER, None
    if not isinstance(given, str):
        raise TypeError(f"ParameterValue.type takes a CwmpType, a type word or None, not {word!r}")
    try:
        member = CwmpType(given)
    except ValueError:
        return CwmpType.OTHER, given
    return (CwmpType.OTHER, given) if member is CwmpType.OTHER else (member, None)


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
    if cwmp_type in (CwmpType.STRING, CwmpType.OTHER):
        return text
    if cwmp_type is CwmpType.DECIMAL:
        if _DECIMAL.fullmatch(text) is None:
            raise ValueError
        return Decimal(text)
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


_TYPE_PAIRS = (OpenEnumPair(CwmpType, CwmpType.OTHER, "type", "type_raw"),)


@dataclass(frozen=True)
class ParameterValue:
    """A ``ParameterValueStruct``: a parameter's full *name*, its *value* and its *type*.

    *value* must match *type*: ``str`` for ``STRING``; an ``int`` (never a ``bool``) within
    the type's range for ``INT`` (32-bit signed), ``UNSIGNED_INT`` (0 to 2**32 - 1),
    ``LONG`` (64-bit signed) and ``UNSIGNED_LONG`` (0 to 2**64 - 1); ``bool`` for
    ``BOOLEAN``; ``datetime`` for ``DATE_TIME`` (a time zone offset in whole minutes; the
    CWMP unknown time is ``0001-01-01T00:00:00Z``); ``bytes`` for ``BASE64`` and
    ``HEX_BINARY``; a finite ``Decimal`` for ``DECIMAL``; ``str`` for ``OTHER``. A value of
    the wrong Python type raises ``TypeError``; a value out of range raises ``ValueError``.

    The type is open (an ``OpenEnumPair``): a type word that names no member becomes
    ``OTHER`` with the word kept verbatim in *type_raw*; a value reported with no type is
    ``OTHER`` with *type_raw* ``None``; an ``OTHER`` value is carried as text. *type_raw* is
    ``None`` unless *type* is ``OTHER``, and the side that changed wins under
    ``dataclasses.replace``. A plain ``str`` naming a member is deprecated (it converts and
    warns), except the ``BASE64`` aliases ``xsd:base64Binary`` and ``soapenc:base64``; a
    driver holding the device's type word uses :meth:`from_text`, which does not warn.
    """

    name: str
    value: CwmpValue
    type: CwmpType
    type_raw: str | None = None
    _type_seen: tuple[tuple[CwmpType, str | None], ...] | None = field(
        default=None, kw_only=True, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        _checks.text("ParameterValue", "name", self.name)
        if not self.name:
            raise ValueError("ParameterValue.name cannot be empty")
        given = cast(object, self.type)
        if isinstance(given, str) and given in _TYPE_ALIASES:
            object.__setattr__(self, "type", _TYPE_ALIASES[given])
        settle(self, _TYPE_PAIRS, "_type_seen")
        _check_value(self.value, self.type)

    @classmethod
    def from_text(cls, name: str, text: str, type: CwmpType | str | None) -> ParameterValue:
        """The value whose XML Schema lexical form is *text*, as a CWMP message carries it.

        *type* is a member, or the type word the device reported (``"xsd:unsignedInt"``,
        any ``BASE64`` spelling), or ``None`` when it reported none: a word naming no member,
        and ``None``, give ``OTHER`` with the text kept as the value. No warning. Reads the
        forms ``text`` writes and the others XML Schema allows: ``1``/``0`` for a boolean,
        a leading ``+`` on a number, lower-case hex digits, more than six fraction digits on
        a dateTime (cut to microseconds). Malformed text raises ``ValueError``.
        """
        member, raw = _type_of(type)
        _checks.text("ParameterValue", "text", text)
        try:
            value = _parse(text, member)
        except (ValueError, KeyError, binascii.Error, InvalidOperation):
            raise ValueError(f"{text!r} is not an {member} value") from None
        return cls(name, value, member, raw)

    @property
    def text(self) -> str:
        """The value's XML Schema lexical form, which :meth:`from_text` reads back:
        ``true``/``false`` for a boolean, decimal digits for a number (no exponent for a
        decimal), ISO 8601 for a dateTime (``Z`` for UTC, the ``+hh:mm`` offset otherwise,
        no zone for a naive ``datetime``, microseconds when not zero), standard base64,
        upper-case hex, the text itself for a string or an ``OTHER`` type."""
        value = self.value
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, datetime):
            return _format_date_time(value)
        if isinstance(value, bytes):
            if self.type is CwmpType.BASE64:
                return base64.b64encode(value).decode("ascii")
            return value.hex().upper()
        if isinstance(value, Decimal):
            return format(value, "f")
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
