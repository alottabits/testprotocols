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
    """

    online: bool
    last_inform_time: datetime | None = None
    cached_manufacturer: str | None = None
    cached_model: str | None = None
    cached_serial_number: str | None = None
    cached_hardware_version: str | None = None
    cached_software_version: str | None = None
