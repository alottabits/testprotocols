"""RADIUS-domain data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import cast, override

from testprotocols.deprecation import MODEL_FRAMES, warn_at_caller
from testprotocols.models._open_enum import OpenEnumPair
from testprotocols.models._open_set import OpenSetPair
from testprotocols.models._sync import Settler, assign, settle


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
    """The ``Acct-Status-Type`` of an accounting record, spelled as the RADIUS attribute
    dictionary spells it: ``Start``, ``Interim-Update`` and ``Stop`` (RFC 2866, the three
    the released contract named), ``Accounting-On``, ``Accounting-Off`` and ``Failed``
    (RFC 2866), the tunnel values of RFC 2867 (``Tunnel-Start`` ... ``Tunnel-Link-Reject``)
    and ``Subsystem-On`` / ``Subsystem-Off`` (IANA RADIUS registry); :attr:`code` is the
    registered number (``None`` for ``OTHER``). The registry has an open assignment policy,
    so the set is open: ``OTHER`` stands for a value this enum does not name, which a
    record keeps in ``RadiusAccountingRecord.record_type_raw``."""

    START = "Start"
    STOP = "Stop"
    INTERIM_UPDATE = "Interim-Update"
    ACCOUNTING_ON = "Accounting-On"
    ACCOUNTING_OFF = "Accounting-Off"
    TUNNEL_START = "Tunnel-Start"
    TUNNEL_STOP = "Tunnel-Stop"
    TUNNEL_REJECT = "Tunnel-Reject"
    TUNNEL_LINK_START = "Tunnel-Link-Start"
    TUNNEL_LINK_STOP = "Tunnel-Link-Stop"
    TUNNEL_LINK_REJECT = "Tunnel-Link-Reject"
    FAILED = "Failed"
    SUBSYSTEM_ON = "Subsystem-On"
    SUBSYSTEM_OFF = "Subsystem-Off"
    OTHER = "other"

    @property
    def code(self) -> int | None:
        """The registered attribute value (``Start`` is 1), or ``None`` for ``OTHER``."""
        return _STATUS_CODES.get(self)


_STATUS_CODES: dict[AcctStatusType, int] = {
    AcctStatusType.START: 1,
    AcctStatusType.STOP: 2,
    AcctStatusType.INTERIM_UPDATE: 3,
    AcctStatusType.ACCOUNTING_ON: 7,
    AcctStatusType.ACCOUNTING_OFF: 8,
    AcctStatusType.TUNNEL_START: 9,
    AcctStatusType.TUNNEL_STOP: 10,
    AcctStatusType.TUNNEL_REJECT: 11,
    AcctStatusType.TUNNEL_LINK_START: 12,
    AcctStatusType.TUNNEL_LINK_STOP: 13,
    AcctStatusType.TUNNEL_LINK_REJECT: 14,
    AcctStatusType.FAILED: 15,
    AcctStatusType.SUBSYSTEM_ON: 18,
    AcctStatusType.SUBSYSTEM_OFF: 19,
}


class AcctTerminateCause(Enum):
    """The ``Acct-Terminate-Cause`` of an accounting record: why a session ended.

    The registered values are ``User-Request`` to ``Host-Request`` (RFC 2866, 1 to 18) and
    ``Supplicant-Restart``, ``Reauthentication-Failure``, ``Port-Reinit`` and
    ``Port-Disabled`` (RFC 3580, 19 to 22) and ``Lost-Power`` (23, IANA RADIUS registry),
    spelled as the attribute dictionary spells them.
    The registry has an open assignment policy, so the set is open: ``OTHER`` stands for a
    cause this enum does not name, which a record keeps in
    ``RadiusAccountingRecord.terminate_cause_raw``.

    A pure ``Enum``: a member does not equal a ``str``, so compare with the member. A
    member's value is its dictionary spelling and :attr:`code` is the registered number
    (``None`` for ``OTHER``). A plain ``str`` naming a member converts in its dictionary
    spelling (``"User-Request"``) or in the registry's prose spelling (``"User Request"``,
    ``"Port Reinitialized"``, ``"Port Administratively Disabled"``, ``"Lost Power"``); the
    match is case-sensitive.
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
    SUPPLICANT_RESTART = "Supplicant-Restart"
    REAUTHENTICATION_FAILURE = "Reauthentication-Failure"
    PORT_REINIT = "Port-Reinit"
    PORT_DISABLED = "Port-Disabled"
    LOST_POWER = "Lost-Power"
    OTHER = "other"

    @property
    def code(self) -> int | None:
        """The registered attribute value (1 for ``User-Request`` ... 22 for ``Port-Disabled``),
        or ``None`` for ``OTHER``."""
        return _TERMINATE_CODES.get(self)

    @classmethod
    @override
    def _missing_(cls, value: object) -> AcctTerminateCause | None:
        member = _prose_cause(value)
        return member


def _prose_cause(value: object) -> AcctTerminateCause | None:
    """The member the registry's prose spelling *value* names, or ``None``: the hyphenated
    dictionary spelling written with spaces, or one of the prose names that differ."""
    if not isinstance(value, str):
        return None
    if value in _PROSE_CAUSES:
        return _PROSE_CAUSES[value]
    if " " in value:
        for member in AcctTerminateCause:
            if member.value == value.replace(" ", "-"):
                return member
    return None


_PROSE_CAUSES: dict[str, AcctTerminateCause] = {
    "Port Reinitialized": AcctTerminateCause.PORT_REINIT,
    "Port Administratively Disabled": AcctTerminateCause.PORT_DISABLED,
}


_TERMINATE_CODES: dict[AcctTerminateCause, int] = {
    AcctTerminateCause.USER_REQUEST: 1,
    AcctTerminateCause.LOST_CARRIER: 2,
    AcctTerminateCause.LOST_SERVICE: 3,
    AcctTerminateCause.IDLE_TIMEOUT: 4,
    AcctTerminateCause.SESSION_TIMEOUT: 5,
    AcctTerminateCause.ADMIN_RESET: 6,
    AcctTerminateCause.ADMIN_REBOOT: 7,
    AcctTerminateCause.PORT_ERROR: 8,
    AcctTerminateCause.NAS_ERROR: 9,
    AcctTerminateCause.NAS_REQUEST: 10,
    AcctTerminateCause.NAS_REBOOT: 11,
    AcctTerminateCause.PORT_UNNEEDED: 12,
    AcctTerminateCause.PORT_PREEMPTED: 13,
    AcctTerminateCause.PORT_SUSPENDED: 14,
    AcctTerminateCause.SERVICE_UNAVAILABLE: 15,
    AcctTerminateCause.CALLBACK: 16,
    AcctTerminateCause.USER_ERROR: 17,
    AcctTerminateCause.HOST_REQUEST: 18,
    AcctTerminateCause.SUPPLICANT_RESTART: 19,
    AcctTerminateCause.REAUTHENTICATION_FAILURE: 20,
    AcctTerminateCause.PORT_REINIT: 21,
    AcctTerminateCause.PORT_DISABLED: 22,
    AcctTerminateCause.LOST_POWER: 23,
}


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


_ACCT_PAIRS = cast(
    "tuple[Settler[tuple[Enum | None, str | None]], ...]",
    (
        OpenEnumPair(AcctStatusType, AcctStatusType.OTHER, "record_type", "record_type_raw"),
        OpenEnumPair(
            AcctTerminateCause,
            AcctTerminateCause.OTHER,
            "terminate_cause",
            "terminate_cause_raw",
            optional=True,
        ),
    ),
)


@dataclass
class RadiusAccountingRecord:
    """A single accounting log entry.

    *record_type* is an :class:`AcctStatusType` and *terminate_cause* an
    :class:`AcctTerminateCause` or ``None`` (present on Stop only). Both registries are
    open: a value that names no member becomes ``OTHER`` and the device's word is kept in
    *record_type_raw* / *terminate_cause_raw*, verbatim and without a warning. A plain
    ``str`` naming a member warns and converts, also on assignment, so a reader holds the
    enum (the RFC's prose spelling of a cause, ``"User Request"``, converts too). The raw
    word is ``None`` unless the field is ``OTHER``; each pair agrees after construction,
    ``replace`` and assignment and the side that changed wins, as for the other open-enum
    fields. A driver that holds such a word builds the member with ``coerce_open_enum``.
    *terminate_cause* members do not equal their text (a pure ``Enum``): compare with the
    member.
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
    record_type_raw: str | None = None
    terminate_cause_raw: str | None = None
    _acct_seen: tuple[tuple[Enum | None, str | None], ...] | None = field(
        default=None, kw_only=True, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        settle(self, _ACCT_PAIRS, "_acct_seen")

    @override
    def __setattr__(self, name: str, value: object) -> None:
        if name == "terminate_cause":
            prose = _prose_cause(value)
            if prose is not None:  # the registry's prose spelling: a deprecated plain string
                warn_at_caller(
                    f"RadiusAccountingRecord.terminate_cause: plain string {value!r} is "
                    f"deprecated; pass AcctTerminateCause.{prose.name}",
                    skip_file_prefixes=MODEL_FRAMES,
                )
                value = prose
        if name == "_acct_seen" or any(pair.owns(name) for pair in _ACCT_PAIRS):
            assign(self, name, value, _ACCT_PAIRS, "_acct_seen")
            return
        object.__setattr__(self, name, value)
