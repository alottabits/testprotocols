"""RADIUS-domain data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import cast, override

from testprotocols.deprecation import MODEL_FRAMES, coerce_enum
from testprotocols.models._open_set import OpenSetPair
from testprotocols.models._sync import assign, settle


class ServiceStatus(StrEnum):
    """The state of a daemon a test controls (``RadiusServer.get_status``)."""

    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class EapMethod(StrEnum):
    """An EAP method a user may authenticate with, spelled as the released contract spells
    it: a tunnelled method and its inner method as ``PEAP-MSCHAPv2`` and ``TTLS-PAP``, a
    stand-alone method as ``EAP-<name>``. The set is open: a server may offer a method
    this enum does not name, which a record keeps verbatim (``RadiusUser`` carries the
    named methods and the unnamed words separately)."""

    PEAP_MSCHAPV2 = "PEAP-MSCHAPv2"
    PEAP_GTC = "PEAP-GTC"
    TTLS_PAP = "TTLS-PAP"
    TTLS_MSCHAPV2 = "TTLS-MSCHAPv2"
    TLS = "EAP-TLS"
    SIM = "EAP-SIM"
    AKA = "EAP-AKA"


class AcctStatusType(StrEnum):
    """The RFC 2866 ``Acct-Status-Type`` of an accounting record, spelled as the
    attribute dictionary spells it. ``Start``, ``Interim-Update`` and ``Stop`` are the
    three the released contract named; ``Accounting-On`` and ``Accounting-Off`` are the
    other values of the RFC 2866 registry a NAS sends when it starts or stops."""

    START = "Start"
    INTERIM_UPDATE = "Interim-Update"
    STOP = "Stop"
    ACCOUNTING_ON = "Accounting-On"
    ACCOUNTING_OFF = "Accounting-Off"


class AcctTerminateCause(Enum):
    """The RFC 2866 ``Acct-Terminate-Cause`` registry (section 5.10): why a session ended.

    A pure ``Enum``: the registry closes the set (values 1 to 18), so there is no
    ``OTHER`` and a member does not equal a ``str``. A member's value is the cause's name
    as the attribute dictionary spells it (``"User-Request"``), and :attr:`code` is the
    RFC's number. A plain ``str`` is converted in either spelling, ``"User-Request"`` or
    the RFC's prose ``"User Request"`` (case-sensitive).
    """

    USER_REQUEST = "User-Request"
    LOST_CARRIER = "Lost-Carrier"
    LOST_SERVICE = "Lost-Service"
    IDLE_TIMEOUT = "Idle-Timeout"
    SESSION_TIMEOUT = "Session-Timeout"
    ADMIN_RESET = "Admin-Reset"
    ADMIN_REBOOT = "Admin-Reboot"
    PORT_ERROR = "Port-Error"
    NAS_ERROR = "NAS-Error"
    NAS_REQUEST = "NAS-Request"
    NAS_REBOOT = "NAS-Reboot"
    PORT_UNNEEDED = "Port-Unneeded"
    PORT_PREEMPTED = "Port-Preempted"
    PORT_SUSPENDED = "Port-Suspended"
    SERVICE_UNAVAILABLE = "Service-Unavailable"
    CALLBACK = "Callback"
    USER_ERROR = "User-Error"
    HOST_REQUEST = "Host-Request"

    @property
    def code(self) -> int:
        """The RFC 2866 attribute value (1 for ``User-Request`` ... 18 for ``Host-Request``)."""
        return list(type(self)).index(self) + 1

    @classmethod
    @override
    def _missing_(cls, value: object) -> AcctTerminateCause | None:
        if isinstance(value, str) and " " in value:
            for member in cls:
                if member.value == value.replace(" ", "-"):
                    return member
        return None


@dataclass
class RadiusServerConfig:
    """Configuration of a registered RADIUS server, as seen from the client side.

    *secret* is intentionally absent — most vendors do not expose it on read,
    and tests should not depend on retrieving it. To verify, re-set it via
    ``RadiusClient.update_server``.
    """

    name: str
    address: str
    port: int  # auth port
    acct_port: int | None  # accounting port, or None if disabled


_EAP_PAIRS = (OpenSetPair(EapMethod, "eap_methods", "eap_methods_known", "eap_methods_unknown"),)


@dataclass
class RadiusUser:
    """A provisioned RADIUS user, as seen from the server side.

    *password* is intentionally absent — same reasoning as RadiusServerConfig.

    The EAP methods are an open set. *eap_methods_known* holds the methods that name an
    :class:`EapMethod` and *eap_methods_unknown* the server's other words, verbatim and
    in order; there is no catch-all member. The released *eap_methods* keeps the full
    word list in its own order and is deprecated: giving it warns. The three agree after
    construction, ``replace`` and assignment, and the side that changed wins: changing
    *eap_methods_known* or *eap_methods_unknown* rewrites the word list silently,
    changing *eap_methods* re-splits the other two and warns. A word names a member
    exactly, letter case included. Both sides given and not agreeing raise
    ``ValueError``; a bare ``str`` for a tuple or list, or a non-member in
    *eap_methods_known*, raises ``TypeError``; an unknown word that names a member
    raises ``ValueError``. A refused assignment changes nothing.
    """

    username: str
    eap_methods: list[str] = field(default_factory=list[str])
    attributes: dict[str, str] = field(default_factory=dict[str, str])
    eap_methods_known: tuple[EapMethod, ...] = ()
    eap_methods_unknown: tuple[str, ...] = ()
    _eap_seen: tuple[tuple[str, ...], ...] | None = field(
        default=None, kw_only=True, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        settle(self, _EAP_PAIRS, "_eap_seen")

    @override
    def __setattr__(self, name: str, value: object) -> None:
        if name == "_eap_seen" or _EAP_PAIRS[0].owns(name):
            assign(self, name, value, _EAP_PAIRS, "_eap_seen")
            return
        object.__setattr__(self, name, value)


@dataclass
class RadiusSession:
    """An active NAS session as tracked by the RADIUS server."""

    session_id: str  # Acct-Session-Id assigned by the NAS
    username: str
    nas_address: str  # IP of the NAS (the AP / switch)
    nas_port: str | None  # NAS-Port-Id, if reported
    calling_station_id: str  # client MAC (canonical lowercase colon-separated)
    called_station_id: str  # AP BSSID + SSID
    start_time: float  # Unix timestamp
    framed_ip_address: str | None  # IP assigned to the client, if known to the server


@dataclass
class RadiusAccountingRecord:
    """A single accounting log entry.

    *record_type* is an :class:`AcctStatusType` and *terminate_cause* an
    :class:`AcctTerminateCause` or ``None`` (present on Stop only). A plain ``str``
    naming one is deprecated: it warns and converts, also on assignment, so a reader
    holds the enum; any other string raises ``ValueError`` listing the legal values (both
    are RFC 2866 registries). Unlike the other enums, *terminate_cause* members do not
    equal their text: compare with the member.
    """

    timestamp: float  # Unix timestamp the record was received
    session_id: str
    username: str
    nas_address: str
    record_type: AcctStatusType | str
    session_time: int | None  # seconds, present on Interim/Stop
    input_octets: int | None
    output_octets: int | None
    input_packets: int | None
    output_packets: int | None
    terminate_cause: AcctTerminateCause | str | None  # present on Stop only

    @override
    def __setattr__(self, name: str, value: object) -> None:
        if name == "record_type":
            value = coerce_enum(
                AcctStatusType,
                cast("AcctStatusType | str", value),
                what="RadiusAccountingRecord.record_type",
                skip_file_prefixes=MODEL_FRAMES,
            )
        elif name == "terminate_cause" and value is not None:
            value = _coerce_cause(value)
        object.__setattr__(self, name, value)


def _coerce_cause(value: object) -> AcctTerminateCause:
    if isinstance(value, AcctTerminateCause):
        return value
    if not isinstance(value, str):
        raise TypeError(
            f"RadiusAccountingRecord.terminate_cause takes an AcctTerminateCause or None, "
            f"not {value!r}"
        )
    return coerce_enum(
        AcctTerminateCause,
        value,
        what="RadiusAccountingRecord.terminate_cause",
        skip_file_prefixes=MODEL_FRAMES,
    )
