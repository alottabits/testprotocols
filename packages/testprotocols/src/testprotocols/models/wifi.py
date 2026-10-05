"""WiFi-domain data models and vocabularies.

The closed vocabularies are enums (``WifiBand``, ``WifiSecurityMode``, ``MfpMode``,
``WifiAclMode``, ``WifiPhyMode``, ``ChannelWidth``, ``MeshRole``); every member equals
the string the released contract used (``WifiBand.GHZ_5 == "5GHz"``). A model field
that holds one is typed ``E | str``: a plain string naming a member is deprecated (it
warns and is converted, also on assignment, so a reader always holds the member) and
any other string raises ``ValueError``. ``WifiStation.capability_flags`` stays
``list[str]``, the device's own words.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum, IntEnum, StrEnum
from typing import ClassVar, cast, override

from testprotocols.deprecation import MODEL_FRAMES, coerce_enum


class WifiBand(StrEnum):
    """A radio band. Identifies a radio on a device (one radio per band)."""

    GHZ_2_4 = "2.4GHz"
    GHZ_5 = "5GHz"
    GHZ_6 = "6GHz"


class WifiSecurityMode(StrEnum):
    """The security of a BSS (the access-point side)."""

    OPEN = "Open"
    OWE = "OWE"
    WPA2_PSK = "WPA2-PSK"
    WPA2_EAP = "WPA2-EAP"
    WPA3_SAE = "WPA3-SAE"
    WPA3_EAP = "WPA3-EAP"
    WPA2_WPA3_PSK_MIXED = "WPA2-WPA3-PSK-Mixed"
    WPA2_WPA3_EAP_MIXED = "WPA2-WPA3-EAP-Mixed"


class MfpMode(StrEnum):
    """Management-frame protection (IEEE 802.11w)."""

    OFF = "off"
    OPTIONAL = "optional"
    REQUIRED = "required"


class WifiAclMode(StrEnum):
    """How a BSS's MAC access-control list is applied."""

    DISABLED = "disabled"  # no MAC filtering; the list is ignored
    ALLOW = "allow"  # allow-list: only listed MACs may associate
    DENY = "deny"  # deny-list: listed MACs are blocked


class WifiPhyMode(StrEnum):
    """An IEEE 802.11 PHY generation (amendment) a radio operates in."""

    A = "a"
    B = "b"
    G = "g"
    N = "n"
    AC = "ac"
    AX = "ax"
    BE = "be"


class ChannelWidth(IntEnum):
    """A channel bandwidth in MHz. The value is the number: ``ChannelWidth(80) == 80``."""

    MHZ_20 = 20
    MHZ_40 = 40
    MHZ_80 = 80
    MHZ_160 = 160
    MHZ_320 = 320


class MeshRole(StrEnum):
    """A mesh participant's role."""

    CONTROLLER = "controller"
    AGENT = "agent"
    CONTROLLER_AND_AGENT = "controller-and-agent"
    UNCOMMISSIONED = "uncommissioned"  # about to be onboarded as an agent


class _EnumFields:
    """Mixin: a model whose ``_ENUM_FIELDS`` are coerced to their enum on assignment (shape 3).

    The generated ``__init__`` assigns each field, so construction, ``replace`` and
    later assignment all go through :meth:`__setattr__`. A plain string naming a
    member warns (the warning points at the caller's construction or assignment
    site); any other string raises ``ValueError`` listing the legal values.
    """

    _ENUM_FIELDS: ClassVar[Mapping[str, type[Enum]]] = {}

    def _coerced(self, name: str, value: object) -> object:
        enum_type = self._ENUM_FIELDS.get(name)
        if enum_type is None:
            return value
        return coerce_enum(
            enum_type,
            cast("Enum | str", value),
            what=f"{type(self).__name__}.{name}",
            skip_file_prefixes=MODEL_FRAMES,
        )

    @override
    def __setattr__(self, name: str, value: object) -> None:
        object.__setattr__(self, name, self._coerced(name, value))


@dataclass
class WifiDfsState:
    """DFS state of a radio.

    A radio is in CAC for ~60s after tuning to a DFS channel; during CAC it
    cannot transmit. Channels on which radar was recently detected enter the
    Non-Occupancy List for ~30 minutes and are unavailable until the NOL ages out.
    """

    is_in_cac: bool
    cac_remaining_seconds: int | None  # None when not in CAC
    nol_channels: list[int] = field(default_factory=list[int])


@dataclass
class WifiCaptiveConfig:
    """Per-BSS captive-portal state."""

    enabled: bool
    redirect_url: str | None


@dataclass
class WifiBssConfig(_EnumFields):
    """Configuration of a single BSS, as returned by WifiBss read methods.

    *passphrase* is intentionally absent — write-only across the contract.
    *band*, *security_mode* and *mfp* are :class:`WifiBand`, :class:`WifiSecurityMode`
    and :class:`MfpMode`; a plain string naming a member is deprecated (it warns and
    is converted) and any other string raises ``ValueError``.
    """

    _ENUM_FIELDS: ClassVar[Mapping[str, type[Enum]]] = {
        "band": WifiBand,
        "security_mode": WifiSecurityMode,
        "mfp": MfpMode,
    }

    name: str  # stable logical handle
    band: WifiBand | str
    ssid: str  # broadcast SSID string
    bssid: str  # MAC address assigned to this BSS
    enabled: bool
    broadcast_enabled: bool
    security_mode: WifiSecurityMode | str
    radius_server_name: str | None  # references RadiusClient registry; None when not Enterprise
    mfp: MfpMode | str
    vlan_id: int | None
    max_clients: int | None
    dtim_period: int
    captive_portal: WifiCaptiveConfig


@dataclass
class WifiStation:
    """An associated station's identity, capabilities, and current stats.

    Stats are point-in-time snapshots; cumulative counters (bytes, packets,
    retries) are since the start of the current association.

    *band* is a :class:`WifiBand`; a plain string naming one is deprecated (it warns
    and is converted) and any other string raises ``ValueError``.

    *capability_flags* are the device's own words, stored as given and in order (for
    example ``["HT", "VHT", "HE"]``, or ``["EHT", "MLO"]`` for Wi-Fi 7).
    """

    mac: str  # canonical: lowercase colon-separated
    bss_name: str  # logical BSS handle the station is associated to
    band: WifiBand | str
    ip_address: str | None  # station's IP if known to the AP (e.g. via DHCP snooping)
    associated_since: float  # Unix timestamp
    rssi_dbm: int
    snr_db: int | None  # None if the driver doesn't report SNR
    tx_rate_mbps: float  # last known PHY rate AP -> station
    rx_rate_mbps: float  # last known PHY rate station -> AP
    tx_bytes: int
    rx_bytes: int
    tx_packets: int
    rx_packets: int
    tx_retries: int
    capability_flags: list[str] = field(default_factory=list[str])

    @override
    def __setattr__(self, name: str, value: object) -> None:
        if name == "band":
            value = coerce_enum(
                WifiBand,
                cast("WifiBand | str", value),
                what="WifiStation.band",
                skip_file_prefixes=MODEL_FRAMES,
            )
        object.__setattr__(self, name, value)


@dataclass
class WifiAcl(_EnumFields):
    """Per-BSS MAC access-control list state. *mode* is a :class:`WifiAclMode`."""

    _ENUM_FIELDS: ClassVar[Mapping[str, type[Enum]]] = {"mode": WifiAclMode}

    bss_name: str
    mode: WifiAclMode | str
    # MACs, canonical lowercase colon-separated
    entries: list[str] = field(default_factory=list[str])


@dataclass
class WifiNeighbor(_EnumFields):
    """A neighbour BSS observed by an off-channel scan.

    *band* is a :class:`WifiBand`. *security_mode* stays free text: it is a
    best-effort identification of a foreign network and may name a scheme no
    :class:`WifiSecurityMode` lists.
    """

    _ENUM_FIELDS: ClassVar[Mapping[str, type[Enum]]] = {"band": WifiBand}

    bssid: str  # MAC, canonical lowercase colon-separated
    ssid: str  # may be empty for hidden SSIDs
    band: WifiBand | str  # the band the scanner observed it on
    channel: int  # operating channel of the neighbour
    rssi_dbm: int
    security_mode: str  # best-effort identification
    last_seen: float  # Unix timestamp of the last beacon/probe-response


@dataclass
class WifiChannelUtilization(_EnumFields):
    """Per-radio channel-utilization breakdown.

    All fields are 0-100. ``busy_pct`` is always populated; the
    component splits (tx/rx/interference) are populated only on drivers
    that report them separately. *band* is a :class:`WifiBand`.
    """

    _ENUM_FIELDS: ClassVar[Mapping[str, type[Enum]]] = {"band": WifiBand}

    band: WifiBand | str
    busy_pct: int  # total channel occupancy
    tx_pct: int | None  # own transmissions
    rx_pct: int | None  # all reception (own BSS + neighbours)
    interference_pct: int | None  # non-WiFi interference, where the driver can distinguish


@dataclass
class WifiRadioStats(_EnumFields):
    """Cumulative per-radio TX/RX/retry counters. *band* is a :class:`WifiBand`."""

    _ENUM_FIELDS: ClassVar[Mapping[str, type[Enum]]] = {"band": WifiBand}

    band: WifiBand | str
    tx_bytes: int
    rx_bytes: int
    tx_packets: int
    rx_packets: int
    tx_retries: int  # retransmitted frames
    tx_failed: int  # frames the driver gave up on (max retries exceeded)


@dataclass
class WifiTransitionConfig:
    """Per-BSS k/v/r configuration snapshot."""

    bss_name: str
    rrm_enabled: bool  # 802.11k
    btm_enabled: bool  # 802.11v
    ft_enabled: bool  # 802.11r
    # 802.11r over-the-DS (True) vs over-the-air (False); meaningful only when ft_enabled
    ft_over_ds: bool


@dataclass
class WifiMeshLink(_EnumFields):
    """A wireless backhaul link between mesh agents. *band* is a :class:`WifiBand`."""

    _ENUM_FIELDS: ClassVar[Mapping[str, type[Enum]]] = {"band": WifiBand}

    band: WifiBand | str
    channel: int
    rssi_dbm: int  # signal strength on the link
    capacity_mbps: float  # estimated PHY-rate capacity in Mbps


@dataclass
class WifiMeshStatus(_EnumFields):
    """A mesh participant's local status snapshot. *role* is a :class:`MeshRole`."""

    _ENUM_FIELDS: ClassVar[Mapping[str, type[Enum]]] = {"role": MeshRole}

    role: MeshRole | str
    enabled: bool
    parent_mac: str | None  # MAC of this agent's parent; None for the controller / root
    hop_count: int  # 0 for the controller; N for an agent N hops away
    backhaul_link: WifiMeshLink | None  # None when no uplink (root) or mesh disabled


@dataclass
class WifiMeshNode(_EnumFields):
    """Identity and position of a mesh agent in the topology. *role* is a :class:`MeshRole`."""

    _ENUM_FIELDS: ClassVar[Mapping[str, type[Enum]]] = {"role": MeshRole}

    mac: str  # canonical lowercase colon-separated
    role: MeshRole | str
    parent_mac: str | None  # None for the controller / root
    hop_count: int


@dataclass
class WifiMeshTopology:
    """The mesh as known to the querying participant.

    Controllers populate the full agent list; pure agents populate
    only the parent + any peers they directly observe.
    """

    controller_mac: str
    agents: list[WifiMeshNode] = field(default_factory=list[WifiMeshNode])
