"""Syslog-destination template.

Defines the abstract contract for configuring where a device sends its syslog
streams and which log roles each destination receives. Small and generic — any
networked device with remote logging can satisfy it — scoped here to the SD-WAN
appliance archetype where event/flow/security logging drives test evidence.

In scope: read/replace the syslog-server list.

Out of scope: reading the log contents themselves (that is the collector's job /
the realtime-syslog path), and security-event retrieval (see ``threat_prevention``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.sdwan_appliance import SyslogServer


@runtime_checkable
class SyslogConfig(Protocol):
    """Abstract contract for configuring syslog destinations."""

    def set_syslog_servers(self, servers: list[SyslogServer]) -> None:
        """Replace the configured syslog-destination list with *servers*."""
        ...

    def get_syslog_servers(self) -> list[SyslogServer]:
        """Return the configured syslog destinations."""
        ...
