"""RADIUS-domain data models."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RadiusServerConfig:
    """Configuration of a registered RADIUS server, as seen from the client side.

    *secret* is intentionally absent — most vendors do not expose it on read,
    and tests should not depend on retrieving it. To verify, re-set it via
    ``RadiusClient.update_server``.
    """

    name: str
    address: str
    port: int                  # auth port
    acct_port: int | None      # accounting port, or None if disabled


@dataclass
class RadiusUser:
    """A provisioned RADIUS user, as seen from the server side.

    *password* is intentionally absent — same reasoning as RadiusServerConfig.
    """

    username: str
    eap_methods: list[str] = field(default_factory=list)
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass
class RadiusSession:
    """An active NAS session as tracked by the RADIUS server."""

    session_id: str            # Acct-Session-Id assigned by the NAS
    username: str
    nas_address: str           # IP of the NAS (the AP / switch)
    nas_port: str | None       # NAS-Port-Id, if reported
    calling_station_id: str    # client MAC (canonical lowercase colon-separated)
    called_station_id: str     # AP BSSID + SSID
    start_time: float          # Unix timestamp
    framed_ip_address: str | None  # IP assigned to the client, if known to the server


@dataclass
class RadiusAccountingRecord:
    """A single accounting log entry."""

    timestamp: float           # Unix timestamp the record was received
    session_id: str
    username: str
    nas_address: str
    record_type: str           # "Start", "Interim-Update", "Stop"
    session_time: int | None   # seconds, present on Interim/Stop
    input_octets: int | None
    output_octets: int | None
    input_packets: int | None
    output_packets: int | None
    terminate_cause: str | None  # present on Stop only
