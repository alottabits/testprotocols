"""WiFi-domain data models."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WifiDfsState:
    """DFS state of a radio.

    A radio is in CAC for ~60s after tuning to a DFS channel; during CAC it
    cannot transmit. Channels on which radar was recently detected enter the
    Non-Occupancy List for ~30 minutes and are unavailable until the NOL ages out.
    """

    is_in_cac: bool
    cac_remaining_seconds: int | None  # None when not in CAC
    nol_channels: list[int] = field(default_factory=list)


@dataclass
class WifiCaptiveConfig:
    """Per-BSS captive-portal state."""

    enabled: bool
    redirect_url: str | None


@dataclass
class WifiBssConfig:
    """Configuration of a single BSS, as returned by WifiBss read methods.

    *passphrase* is intentionally absent — write-only across the contract.
    """

    name: str                   # stable logical handle
    band: str
    ssid: str                   # broadcast SSID string
    bssid: str                  # MAC address assigned to this BSS
    enabled: bool
    broadcast_enabled: bool
    security_mode: str
    radius_server_name: str | None  # references RadiusClient registry; None when not Enterprise
    mfp: str                    # "off" | "optional" | "required"
    vlan_id: int | None
    max_clients: int | None
    dtim_period: int
    captive_portal: WifiCaptiveConfig


@dataclass
class WifiStation:
    """An associated station's identity, capabilities, and current stats.

    Stats are point-in-time snapshots; cumulative counters (bytes, packets,
    retries) are since the start of the current association.
    """

    mac: str                       # canonical: lowercase colon-separated
    bss_name: str                  # logical BSS handle the station is associated to
    band: str                      # "2.4GHz" / "5GHz" / "6GHz"
    ip_address: str | None         # station's IP if known to the AP (e.g. via DHCP snooping)
    associated_since: float        # Unix timestamp
    rssi_dbm: int
    snr_db: int | None             # None if the driver doesn't report SNR
    tx_rate_mbps: float            # last known PHY rate AP -> station
    rx_rate_mbps: float            # last known PHY rate station -> AP
    tx_bytes: int
    rx_bytes: int
    tx_packets: int
    rx_packets: int
    tx_retries: int
    capability_flags: list[str] = field(default_factory=list)
    # capability_flags examples: ["HT", "VHT", "HE"], or ["EHT", "MLO"] for Wi-Fi 7


@dataclass
class WifiAcl:
    """Per-BSS MAC access-control list state."""

    bss_name: str
    mode: str                      # "disabled" | "allow" | "deny"
    entries: list[str] = field(default_factory=list)  # MACs, canonical lowercase colon-separated


@dataclass
class WifiNeighbor:
    """A neighbour BSS observed by an off-channel scan."""

    bssid: str                     # MAC, canonical lowercase colon-separated
    ssid: str                      # may be empty for hidden SSIDs
    band: str                      # the band the scanner observed it on
    channel: int                   # operating channel of the neighbour
    rssi_dbm: int
    security_mode: str             # best-effort identification
    last_seen: float               # Unix timestamp of the last beacon/probe-response


@dataclass
class WifiChannelUtilization:
    """Per-radio channel-utilization breakdown.

    All fields are 0-100. ``busy_pct`` is always populated; the
    component splits (tx/rx/interference) are populated only on drivers
    that report them separately.
    """

    band: str
    busy_pct: int                  # total channel occupancy
    tx_pct: int | None             # own transmissions
    rx_pct: int | None             # all reception (own BSS + neighbours)
    interference_pct: int | None   # non-WiFi interference, where the driver can distinguish


@dataclass
class WifiRadioStats:
    """Cumulative per-radio TX/RX/retry counters."""

    band: str
    tx_bytes: int
    rx_bytes: int
    tx_packets: int
    rx_packets: int
    tx_retries: int                # retransmitted frames
    tx_failed: int                 # frames the driver gave up on (max retries exceeded)


@dataclass
class WifiTransitionConfig:
    """Per-BSS k/v/r configuration snapshot."""

    bss_name: str
    rrm_enabled: bool              # 802.11k
    btm_enabled: bool              # 802.11v
    ft_enabled: bool               # 802.11r
    ft_over_ds: bool               # 802.11r over-the-DS (True) vs over-the-air (False); meaningful only when ft_enabled


@dataclass
class WifiMeshLink:
    """A wireless backhaul link between mesh agents."""

    band: str                      # "2.4GHz" / "5GHz" / "6GHz"
    channel: int
    rssi_dbm: int                  # signal strength on the link
    capacity_mbps: float           # estimated PHY-rate capacity in Mbps


@dataclass
class WifiMeshStatus:
    """A mesh participant's local status snapshot."""

    role: str                      # "controller" | "agent" | "controller-and-agent" | "uncommissioned"
    enabled: bool
    parent_mac: str | None         # MAC of this agent's parent; None for the controller / root
    hop_count: int                 # 0 for the controller; N for an agent N hops away
    backhaul_link: WifiMeshLink | None  # None when no uplink (root) or mesh disabled


@dataclass
class WifiMeshNode:
    """Identity and position of a mesh agent in the topology."""

    mac: str                       # canonical lowercase colon-separated
    role: str                      # "controller" | "agent" | "controller-and-agent"
    parent_mac: str | None         # None for the controller / root
    hop_count: int


@dataclass
class WifiMeshTopology:
    """The mesh as known to the querying participant.

    Controllers populate the full agent list; pure agents populate
    only the parent + any peers they directly observe.
    """

    controller_mac: str
    agents: list[WifiMeshNode] = field(default_factory=list)
