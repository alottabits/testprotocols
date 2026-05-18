"""TR-069 ACS data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CpeConnectionStatus:
    """ACS-side view of a CPE record.

    Reflects what the ACS believes about the CPE — not a live probe.
    All fields remain populated when the CPE is offline (from the
    last successful Inform). ``last_inform_time`` is ``None`` only
    when the ACS has never received an Inform from this CPE.

    ``last_boot_time`` is set to the timestamp of the most recent
    Boot Inform (CWMP informEvent "1 BOOT") the ACS received from
    this CPE. Use it to confirm a reboot has actually completed —
    comparing successive ``last_boot_time`` values against a baseline
    is the most reliable post-reboot re-registration signal because
    the ACS keeps the previous CPE record indefinitely (a presence
    check via list_cpes() would trivially pass against the stale
    pre-reboot record).
    """

    online: bool
    last_inform_time: datetime | None = None
    last_boot_time: datetime | None = None
    cached_manufacturer: str | None = None
    cached_model: str | None = None
    cached_serial_number: str | None = None
    cached_hardware_version: str | None = None
    cached_software_version: str | None = None
