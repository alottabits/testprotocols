"""Threat-prevention template — IDS/IPS, anti-malware, and security events.

Defines the abstract contract for a managed SD-WAN appliance's threat-prevention
subsystem: configuring intrusion detection/prevention and anti-malware, and
reading back security events.

Security-event reads here are the *deferred*, settle-aware augmentation surface;
realtime assertions in a testbed should still use the syslog backbone. Events
carry only normalized fields (action + category, not vendor signature ids).

In scope: intrusion mode/sensitivity, malware mode, security-event retrieval.

Out of scope: firewall rules (see ``l3_firewall`` / ``l7_firewall``), content
filtering (see ``content_filtering``), and syslog destination config (see
``syslog_config``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.sdwan_appliance import (
    IntrusionConfig,
    IntrusionMode,
    IntrusionSensitivity,
    MalwareConfig,
    MalwareMode,
    SecurityEvent,
)


@runtime_checkable
class ThreatPrevention(Protocol):
    """Abstract contract for an appliance's IDS/IPS + anti-malware subsystem."""

    def set_intrusion(
        self, mode: IntrusionMode, sensitivity: IntrusionSensitivity | None = None
    ) -> None:
        """Set the IDS/IPS *mode* and optional ruleset *sensitivity*."""
        ...

    def get_intrusion(self) -> IntrusionConfig:
        """Return the current IDS/IPS configuration."""
        ...

    def set_malware(self, mode: MalwareMode) -> None:
        """Enable or disable anti-malware protection."""
        ...

    def get_malware(self) -> MalwareConfig:
        """Return the current anti-malware configuration."""
        ...

    def get_security_events(self, since_s: int = 3600) -> list[SecurityEvent]:
        """Return security events from the last *since_s* seconds.

        Deferred / settle-aware augmentation surface — not the realtime
        assertion path. Empty list when none.
        """
        ...
